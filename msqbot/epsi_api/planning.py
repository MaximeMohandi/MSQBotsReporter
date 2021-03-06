import epsi_api.edt_parser as edt_parser
import exception as common_error
from bs4 import BeautifulSoup
from datetime import datetime
import requests


PLANNING_URI = 'https://edtmobiliteng.wigorservices.net//WebPsDyn.aspx?action=posEDTBEECOME&serverid=C&Tel=maxime' \
               '.mohandi&date={} '


def get_week_courses():
    """Get the planning for the current week

    Returns
    -------
        :class:`list`
            A list of courses planned this week
    """
    try:
        request = PLANNING_URI.format(edt_parser.clean_start_day())
        response = requests.get(request)
        soup = BeautifulSoup(response.text, "html.parser")
        week_courses = edt_parser.parse_epsi_planning_html(soup)
        return __format_courses__(week_courses)

    except requests.ConnectionError:
        raise common_error.HttpError


def get_week_courses_for(date):
    """ Get the planning for the given date

    Parameters
    -----------
        date: :class:`str`
            a day in the wanted week

    Returns
    -------
        :class:`list`
            A list of course planned into the given day
    """
    try:
        week_date = datetime.strptime(date, '%d/%m/%Y').strftime('%m/%d/%y')
        request = PLANNING_URI.format(week_date)
        response = requests.get(request)
        soup = BeautifulSoup(response.text, "html.parser")
        planning = edt_parser.parse_epsi_planning_html(soup)
        return __format_courses__(planning)

    except requests.ConnectionError:
        raise common_error.HttpError


def get_today_courses():
    """Get the courses planned for the current day

    Returns
    -------
        :class:`list`
            list of course planned for the current day
    """
    today_formatted = datetime.today().strftime('%m/%d/%y')
    return get_courses_for(today_formatted)


def get_courses_for(date):
    """Get the courses planned for a given day

    Parameters
    -----------
        date: :class:`str`
            the day to get course

    Returns
    -------
        :class:`list`
            A list of courses planned for the given day

    """
    try:
        given_date = datetime.strptime(date, '%d/%m/%y').strftime('%m/%d/%y')
        request = PLANNING_URI.format(given_date)
        response = requests.get(request)
        soup = BeautifulSoup(response.text, "html.parser")

        planned_course_date = edt_parser.parse_epsi_planning_html(soup)

        for course in planned_course_date:
            course_date = edt_parser.literal_french_date_to_us_date_converter(course['date'])
            if course_date == given_date:
                return __format_courses__([course])  # put course into array to use it with format_courses
    except requests.ConnectionError:
        raise common_error.HttpError


def get_next_classroom():
    """ get the classroom number for the next course of the current day

    Returns
    -------
        :class:`int`
            The next classroom number
    """
    current_hour = datetime.now().hour
    course_planned_today = get_today_courses()['course']

    if course_planned_today is not None:
        for course in course_planned_today:
            start_hour = int(course['hours'].split('-')[0].split(':')[0])  # parse the result list to get the begining hour
            end_hour = int(course['hours'].split('-')[1].split(':')[0].split(' ')[1])  # parse the result list to get the ending hour

            if start_hour <= current_hour < end_hour:
                return course['room']


def __format_courses__(planning_details):
    """ format the html parsed result into a comprehensible list of courses

    Parameters
    -----------
        planning_details: :class:`list`
            Raw result of timetable parsed html

    The list contain a dictionnary with the following elements:
        - title `str` : It's the title of the course
        - courses `dict`: This is a dictionnary contaning course details
            - hoursecourse `tuple`: begin and end hours
            - courselabel `str`: course name
            - courseroom `str`: room where the course is
            - courseteacher `str`: name of the teacher


    Returns
    -------
        :class:`list`
            List representing the a day with the courses associated
    """
    return [{
        'title': planned['date'],
        'courses': [{
            'hourscourse': course['hours'],
            'courselabel': course['label'],
            'courseroom': course['room'],
            'courseteacher': course['prof']
        }for course in planned['course']]
    }for planned in planning_details]
