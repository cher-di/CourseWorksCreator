import logging
import io

from enum import Enum

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload


__all__ = [
    'Classroom',

    'ClassroomError',
    'FileTooLarge',

    'SubmissionState',
    'CourseWorkType',
]

logger = logging.getLogger('grader.classroom')

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',  # read info about courses
    'https://www.googleapis.com/auth/classroom.coursework.students',  # get course works and grade them
    'https://www.googleapis.com/auth/classroom.rosters.readonly',  # get students info
    'https://www.googleapis.com/auth/classroom.profile.emails',  # get students email

    'https://www.googleapis.com/auth/drive.readonly',  # download labs from drive
]


class SubmissionState(Enum):
    SUBMISSION_STATE_UNSPECIFIED = 'SUBMISSION_STATE_UNSPECIFIED'
    NEW = 'NEW'
    CREATED = 'CREATED'
    TURNED_IN = 'TURNED_IN'
    RETURNED = 'RETURNED'
    RECLAIMED_BY_STUDENT = 'RECLAIMED_BY_STUDENT'


class CourseWorkType(Enum):
    COURSE_WORK_TYPE_UNSPECIFIED = 'COURSE_WORK_TYPE_UNSPECIFIED'
    ASSIGNMENT = 'ASSIGNMENT'
    SHORT_ANSWER_QUESTION = 'SHORT_ANSWER_QUESTION'
    MULTIPLE_CHOICE_QUESTION = 'MULTIPLE_CHOICE_QUESTION'


class ClassroomError(Exception):
    pass


class FileTooLarge(ClassroomError):
    pass


class Classroom:
    def __init__(self, token: str, subject: str):
        credentials = service_account.Credentials.from_service_account_file(token,
                                                                            subject=subject,
                                                                            scopes=SCOPES)
        self._classroom_service = build('classroom', 'v1', credentials=credentials)
        self._drive_service = build('drive', 'v3', credentials=credentials)

    def list_courses(self):
        results = self._classroom_service.courses().list().execute()
        return results.get('courses', [])

    def get_course(self, course_id: str):
        return self._classroom_service.courses().get(id=course_id).execute()

    def list_course_works(self, course_id: str):
        results = self._classroom_service.courses().courseWork().list(courseId=course_id).execute()
        return results.get('courseWork', [])

    def get_course_work(self, course_id: str, course_work_id: str):
        return self._classroom_service.courses().courseWork().get(courseId=course_id,
                                                                  id=course_work_id).execute()

    def create_course_work(self, course_id: str, body: dict):
        return self._classroom_service.courses().courseWork().create(courseId=course_id,
                                                                     body=body).execute()

    def list_student_submissions(self,
                                 course_id: str,
                                 course_work_id: str,
                                 state: SubmissionState = None):
        request_params = {
            'courseId': course_id,
            'courseWorkId': course_work_id,
        }
        if state:
            request_params['states'] = state.value
        results = self._classroom_service.courses().courseWork().studentSubmissions().list(**request_params).execute()
        return results.get('studentSubmissions', [])

    def get_student_submission(self,
                               course_id: str,
                               course_work_id: str,
                               student_submission_id: str):
        return self._classroom_service.courses().courseWork().studentSubmissions().get(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=student_submission_id
        ).execute()

    def list_students(self, course_id: str):
        result = self._classroom_service.courses().students().list(id=course_id).execute()
        return result.get('students', [])

    def get_student(self, course_id: str, user_id: str):
        result = self._classroom_service.courses().students().get(courseId=course_id,
                                                                  userId=user_id).execute()
        return result['profile']

    def get_user_profile(self, user_id: str):
        return self._classroom_service.userProfiles().get(userId=user_id).execute()

    def download_lab(self, file_id: str, max_file_size: int) -> bytes:
        request = self._drive_service.files().get_media(fileId=file_id)
        chunk_size = 1024 * 1024 * 10
        curr_file_size = 0
        with io.BytesIO() as file_handler:
            downloader = MediaIoBaseDownload(file_handler, request, chunksize=chunk_size)
            done = False
            while not done:
                _, done = downloader.next_chunk()
                curr_file_size += chunk_size
                logger.debug(f'Downloaded {curr_file_size} bytes')
                if curr_file_size > max_file_size:
                    raise FileTooLarge()
            return file_handler.getvalue()

    def patch_draft_grade(self, submission: dict, grade: int):
        return self._classroom_service.courses().courseWork().studentSubmissions().patch(
            courseId=submission['courseId'],
            courseWorkId=submission['courseWorkId'],
            id=submission['id'],
            body={**submission, **{
                'draftGrade': grade,
            }},
            updateMask='draftGrade'
        ).execute()

    def patch_assigned_grade(self, submission: dict, grade: int):
        return self._classroom_service.courses().courseWork().studentSubmissions().patch(
            courseId=submission['courseId'],
            courseWorkId=submission['courseWorkId'],
            id=submission['id'],
            body={**submission, **{
                'assignedGrade': grade,
            }},
            updateMask='assignedGrade'
        ).execute()
