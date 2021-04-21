import argparse
import os
import json

from .classroom import *
from . import PROJECT_ROOT

TOKEN = os.path.join(PROJECT_ROOT, 'credentials.json')
SUBJECT = os.path.join(PROJECT_ROOT, 'subject.txt')


def print_output(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        try:
            output = json.dumps(result, indent=2)
        except Exception:
            output = str(result)
        print(output)
        return result
    return wrapper


@print_output
def list_courses(args: argparse.Namespace, classroom: Classroom) -> list:
    return classroom.list_courses()


@print_output
def list_course_works(args: argparse.Namespace, classroom: Classroom) -> list:
    return classroom.list_course_works(args.course_id)


@print_output
def list_submissions(args: argparse.Namespace, classroom: Classroom) -> list:
    return classroom.list_student_submissions(args.course_id, args.course_work_id)


@print_output
def create_course_work(args: argparse.Namespace, classroom: Classroom) -> dict:
    return classroom.create_course_work(args.course_id,
                                        body={
                                            'title': args.course_work_title,
                                            'workType': 'ASSIGNMENT',
                                            'state': 'PUBLISHED',
                                            'maxPoints': args.max_points,
                                        })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser('CourseCreator', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers()

    list_courses_parser = subparsers.add_parser('list_courses')
    list_courses_parser.set_defaults(func=list_courses)

    list_course_works_parser = subparsers.add_parser('list_course_works')
    list_course_works_parser.add_argument('course_id',
                                          help='Course ID')
    list_course_works_parser.set_defaults(func=list_course_works)

    list_submissions_parser = subparsers.add_parser('list_submissions')
    list_submissions_parser.add_argument('course_id',
                                         help='Course ID')
    list_submissions_parser.add_argument('course_work_id',
                                         help='CourseWork ID')
    list_submissions_parser.set_defaults(func=list_submissions)

    create_course_parser = subparsers.add_parser('create_course_work')
    create_course_parser.add_argument('course_id',
                                      help='Course ID')
    create_course_parser.add_argument('course_work_title',
                                      help='CourseWork title')
    create_course_parser.add_argument('--max-points',
                                      dest='max_points',
                                      help='Max points',
                                      type=int,
                                      default=100)
    create_course_parser.set_defaults(func=create_course_work)

    return parser.parse_args()


def main():
    args = parse_args()

    for filepath in TOKEN, SUBJECT:
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
        elif not os.path.isfile(filepath):
            raise IsADirectoryError(filepath)
        elif not os.access(filepath, os.R_OK):
            raise Exception(f'Have no right to read {filepath}')

    with open(SUBJECT, 'r') as subject_file:
        subject = subject_file.read()

    classroom = Classroom(TOKEN, subject)

    args.func(args, classroom)


if __name__ == '__main__':
    main()
