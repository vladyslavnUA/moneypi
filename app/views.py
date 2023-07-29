from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Employee, WorkRecord
from .forms import ClockInForm, ClockOutForm
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
from django.db.models import Q, F
from datetime import datetime
from textblob import TextBlob
import csv
from django.http import HttpResponse


@login_required
def employee_dashboard(request):
    employee = request.user.employee
    work_records = WorkRecord.objects.filter(employee=employee).order_by('-date')
    return render(request, 'app/employee_dashboard.html', {'work_records': work_records})


def home(request):
    employees = Employee.objects.all()
    
    query = request.GET.get('q')
    
    if query:
        work_records = WorkRecord.objects.filter(
            Q(employee__name__icontains=query) | Q(date__icontains=query)
        )
    else:
        work_records = WorkRecord.objects.all()

    ######### SEARCH
    # Get search parameters from the URL query string
    employee_name = request.GET.get('employee')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    clock_in_time = request.GET.get('clock_in_time')
    clock_out_time = request.GET.get('clock_out_time')
    total_hours = request.GET.get('total_hours')
    has_clock_out = request.GET.get('has_clock_out')

    # Filter work records based on search criteria
    if employee_name:
        employees = employees.filter(name__icontains=employee_name)

    if start_date:
        employees = employees.filter(workrecord__date__gte=start_date)

    if end_date:
        employees = employees.filter(workrecord__date__lte=end_date)

    if clock_in_time:
        employees = employees.filter(workrecord__clock_in__time__icontains=clock_in_time)

    if clock_out_time:
        employees = employees.filter(workrecord__clock_out__time__icontains=clock_out_time)

    if total_hours:
        employees = employees.filter(workrecord__total_hours__icontains=total_hours)

    if has_clock_out:
        employees = employees.filter(workrecord__clock_out__isnull=False)


    sort_by = request.GET.get('sort_by')
    if sort_by:
        employees = employees.order_by(F(sort_by).asc() if sort_by.startswith('-') else F(sort_by).desc())


    ###############

    # Set the number of records to display per page (e.g., 10 records per page)
    records_per_page = 10
    paginator = Paginator(WorkRecord.objects.all(), records_per_page)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    # Pagination
    page_number = request.GET.get('page', 1)  # Get the current page number from the URL query parameter 'page'
    paginator = Paginator(employees, 10)  # Show 10 employees per page
    page_obj = paginator.get_page(page_number)

    # Calculate total work hours for each employee
    for employee in employees:
        work_records = WorkRecord.objects.filter(employee=employee)
        total_hours = 0
        for record in work_records:
            if record.clock_out:
                total_hours += (record.clock_out - record.clock_in).total_seconds() / 3600
        employee.total_hours = total_hours

    # Perform sentiment analysis on employee comments
    for employee in employees:
        work_records = WorkRecord.objects.filter(employee=employee)
        total_hours = 0
        sentiment_score = 0
        comment_count = 0

        for record in work_records:
            if record.clock_out:
                total_hours += (record.clock_out - record.clock_in).total_seconds() / 3600

            if record.comments:
                blob = TextBlob(record.comments)
                sentiment_score += blob.sentiment.polarity
                comment_count += 1

        # Calculate average sentiment score for employee comments
        if comment_count > 0:
            average_sentiment = sentiment_score / comment_count
            employee.average_sentiment = round(average_sentiment, 2)
        else:
            employee.average_sentiment = 0

        employee.total_hours = total_hours

    return render(request, 'app/index.html', {'employees': employees, 'page_obj': page_obj, 'query': query})

# geo
def get_location_from_address(address):
    geolocator = Nominatim(user_agent="work_hours_tracking_app")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

@login_required
def clock_in_out(request):
    employe = request.user
    employee = Employee.objects.filter(name=employe)
    context = {}

    if request.method == 'POST':
        form = ClockInForm(request.POST)
        if form.is_valid():
                clock_in_form = ClockInForm(request.POST)
                clock_out_form = ClockOutForm(request.POST)

                if clock_in_form.is_valid() and clock_out_form.is_valid():
                    clock_in_address = clock_in_form.cleaned_data.get('address')
                    clock_out_address = clock_out_form.cleaned_data.get('address')

                    clock_in_latitude, clock_in_longitude = get_location_from_address(clock_in_address)
                    clock_out_latitude, clock_out_longitude = get_location_from_address(clock_out_address)

                    if clock_in_latitude and clock_in_longitude:
                        # Save the clock-in location to the WorkRecord model
                        work_record = WorkRecord.objects.create(
                        employee=employee,
                        clock_in_address=clock_in_address,
                        clock_in_latitude=clock_in_latitude,
                        clock_in_longitude=clock_in_longitude,
                    )
                    work_record.save()

                if clock_out_latitude and clock_out_longitude:
                    # Save the clock-out location to the WorkRecord model
                    work_record = WorkRecord.objects.filter(employee=employee).latest('date')
                    work_record.clock_out_address = clock_out_address
                    work_record.clock_out_latitude = clock_out_latitude
                    work_record.clock_out_longitude = clock_out_longitude
                    work_record.save()

                return redirect('home')

        else:
            clock_in_form = ClockInForm()
            clock_out_form = ClockOutForm()
            context['clock_in_form'] = clock_in_form
            context['clock_out_form'] = clock_out_form

    return render(request, 'app/clock_in_out.html', )

def clock_in(request):
    if request.method == 'POST':
        form = ClockInForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee']
            employee = Employee.objects.get(pk=employee_id)
            clock_in_time = datetime.now()

            # Get the latitude and longitude coordinates of the clock-in location
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']

            # Create a Point object to store the clock-in location
            clock_in_location = Point(longitude, latitude)

            # Save the clock-in location to the WorkRecord model
            WorkRecord.objects.create(
                employee=employee,
                clock_in=clock_in_time,
                clock_in_location=clock_in_location
            )

            return redirect('home')
    else:
        form = ClockInForm()
    return render(request, 'app/clock_in.html', {'form': form})

def clock_out(request):
    if request.method == 'POST':
        form = ClockOutForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee']
            employee = Employee.objects.get(pk=employee_id)
            clock_out_time = datetime.now()

            # Get the latitude and longitude coordinates of the clock-out location
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']

            # Create a Point object to store the clock-out location
            clock_out_location = Point(longitude, latitude)

            # Save the clock-out location to the WorkRecord model
            work_record = WorkRecord.objects.filter(employee=employee, clock_out__isnull=True).order_by('-clock_in').first()
            if work_record:
                work_record.clock_out = clock_out_time
                work_record.clock_out_location = clock_out_location
                work_record.save()

            return redirect('home')

    else:
        form = ClockOutForm()
    return render(request, 'app/clock_out.html', {'form': form})

def calendar_view(request):
    # Implement logic to retrieve work records and calculate total hours per employee

    employees = Employee.objects.all()
    data = []
    for employee in employees:
        total_hours = 0
        work_records = WorkRecord.objects.filter(employee=employee)
        for record in work_records:
            if record.clock_out:
                total_hours += (record.clock_out - record.clock_in).total_seconds() / 3600
        data.append((employee.name, total_hours))

    # Create the bar chart
    labels, hours = zip(*data)
    plt.bar(labels, hours)
    plt.xlabel('Employee')
    plt.ylabel('Total Hours')
    plt.title('Total Work Hours per Employee')
    plt.xticks(rotation=45)

    # Save the chart to an image file
    chart_path = 'app/static/chart.png'
    plt.tight_layout()
    plt.savefig(chart_path)

    return render(request, 'app/calendar.html', {'chart_path': chart_path})

def reports(request):
    employees = Employee.objects.all()
    return render(request, 'app/reports.html', {'employees': employees})

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="work_hours_report.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write header row
    writer.writerow(['Employee', 'Date', 'Clock In', 'Clock Out'])

    # Write data rows
    work_records = WorkRecord.objects.all()
    for record in work_records:
        employee = record.employee.name
        date = record.date
        clock_in = record.clock_in.strftime('%Y-%m-%d %H:%M:%S')
        clock_out = record.clock_out.strftime('%Y-%m-%d %H:%M:%S') if record.clock_out else ''
        writer.writerow([employee, date, clock_in, clock_out])

    return response