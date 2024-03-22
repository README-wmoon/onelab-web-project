import json
import secrets
import smtplib
import ssl
import string
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from sys import platform

from django.db.models import Sum, F, Q
from rest_framework.templatetags.rest_framework import data

from exhibition.models import Exhibition
from notification.models import Notification
from school.models import School
from visitRecord.models import VisitRecord

ssl._create_default_https_context = ssl._create_unverified_context

from allauth.socialaccount.models import SocialAccount
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from member.models import Member, MemberFile
from member.serializers import MemberSerializer
from oneLabProject import settings
from university.models import University




class MemberCheckIdView(APIView):
    # get으로 받는다
    def get(self, request):
        # 멤버 아이디를 다른 곳에서 받는다.
        member_id = request.GET['member-id']
        # 멤버 아이디가 존재 했을 때 쓰인다.
        is_duplicated = Member.objects.filter(member_id=member_id).exists()
        return Response({'isDup': is_duplicated})

# 일반 회원가입
class MemberNormalJoinView(View):
    # get으로 받는다.
    def get(self, request):
        # context에서 맴버 이메일이랑 학교 이메일, 아이디를 넣는다.
        context = {
            'memberEmail': request.GET.get('member_email'),
            'memberSchoolEmail': request.GET.get('member_school_email'),
            'id': request.GET.get('id')
        }

        # render로 쓰여 context를 보내준다.
        return render(request, 'login/normal-student-join.html', context)

    @transaction.atomic
    def post(self, request):

        # request.POST안에 data 값을 넣는다
        data = request.POST
        # university 테이블에 있는 university-member-major를 변수에 넣는다.
        university_major = data['university-member-major']

        # 멤버 data를 받아온다.
        data = {
            'member_name': data['member-name'],
            'member_password': data['member-password'],
            'member_email': data['member-email'],
            'member_school_email': data['member-school-email'],
            'member_phone': data['member-phone'],

        }

        # data 안에 있는 Member를 데이터 안에 넣는다.
        member = Member.objects.create(**data)

        # member = Member.objects.filter(id=request.POST.get('id'))
        # # OAuth 최초 로그인 후 회원가입 시
        # if member.exists():
        #     del data['member_email']
        #     data['updated_date'] = timezone.now()
        #     member.update(**data)
        #
        # else:
        #     member = Member.objects.create(**data)

        # 맴버 아이디를 가져온다.
        member = Member.objects.get(id=member.id)

        # university 테이블에 있는 원하는 데이터를 넣는다.
        # 위에 쓰였던 멤버 테이블도 같이 넣는다.
        university_info = {
            'university_member_birth': "1999-09-22",
            'university_member_major': university_major,
            'member': member
        }
        print(university_info)


        # university_info 안에 있는 것을 다 추가시켜준다.
        University.objects.create(**university_info)

        return redirect('member:login')


class MemberJoinView(View):
    def get(self, request):
        print(request.GET.get('member_name'))

        # context 안에 맴버 정보들을 받는다.
        context = {
            'memberEmail': request.GET.get('member_email'),
            'memberType': request.GET.get('member_type'),
            'memberName': request.GET.get('member_name'),
            'memberPhone': request.GET.get('member_phone'),
            'memberSchoolEmail': request.GET.get('member_school_email')
        }
        # member_info = request.session['join-member-data']
        # context = {
        #     'member_email': member_info['member_email'],
        #     'member_name': member_info['member_name']
        # }

        # render로 context를 보내준다.
        return render(request, 'login/college-student-join.html', context)

    @transaction.atomic
    def post(self, request):

        # request.POST를 data로 넣는다.
        data = request.POST
        user = SocialAccount.objects.get(user=request.user)

        # university 테이블 안에 있는 데이터를 변수안에 넣는다.
        university_major = data['university-member-major']

        # data 안에 테이블 데이터를 받아온다.
        data = {
            # 'member_name': data['member-name'],
            'member_phone': data['member-phone'],
            # 'member_password': data['member-password'],
            # 'member_email': data['member-email'],
            'member_school_email': data['member-school-email'],
        }

        # 가장 최근에 생성된 아이디를 변수 안에 넣는다.
        last_member = Member.objects.latest('id')

        # OAuth 검사
        # OAuth 최초 로그인 시 TBL_MEMBER에 INSERT된 회원 ID가 member_id 이다.
        member = Member.objects.filter(id=last_member.id, member_type='naver')
        #   1. 아이디는 중복이 없다
        #   2. 이메일과 타입에 중복이 있다.
        #   3. OAuth로 최초 로그인된 회원을 찾아라

        # OAuth 최초 로그인 후 회원 가입
        if member.exists():
            print("존재함")
            # del data['member_email']
            # data['updated_date'] = timezone.now()
            member.update(**data)

        else:
            print("존재함1")
            member = Member.objects.create(**data)

        # 가장 최근에 검색된 id를 가지고 와 member변수 안에 넣는다.
        member = Member.objects.get(id=last_member.id)

        # university_info안에 university 테이블에 데이터, member 데이터를 넣어준다.
        university_info = {
            'university_member_birth': "1999-09-22",
            'university_member_major': university_major,
            'member': member
        }
        print(university_info, member.__dict__)

        # university_info를 추가시켜준다.
        University.objects.create(**university_info)

        # redirect로 로그인 페이지로 넘겨준다.
        return redirect('member:login')


class MemberLoginView(View):
    def get(self, request):

        # render로 로그인 페이지로 넘겨준다.
        return render(request, 'login/login.html')

    def post(self, request):
        # request.POST를 변수안에 넣어준다.
        data = request.POST

        # data안에 이메일이랑 패스워드를 가져온다
        # 로그인 페이지에는 이메일과 패스워드 밖에 안가져와서
        data = {
            'member_email': data['member-email'],
            'member_password': data['member-password']
        }

        # 맴버 이메일과 맴버 패스워드를 필터링을 거쳐 member라는 변수 안에 넣어준다.
        member = Member.objects.filter(member_email=data['member_email'], member_password=data['member_password'])
        # print(member)
        url = '/'

        # 맴버 이메일과 패스워드가 존재하면 (성공)
        if member.exists():
            # 성공
            # MemberSerializer(member.first()).data는 선택된 멤버 객체를 시리얼라이즈하여 JSON 형식으로 변환합니다.
            # 맴버테이블의 첫번쨰를 가져와서 맴버가 있는 색션에 넣어준다.
            request.session['member'] = MemberSerializer(member.first()).data
            url = '/'

            # 메인페이지로 넘겨준다.
            return redirect('/')

        # 안되면 로그인 페이지로 다시 보내준다.
        # JS 부분에 check=False를 쓰여서 유효성 검사를 해준다.
        return render(request, 'login/login.html', {'check': False})


class SendVerificationCodeView(APIView):
    def post(self, request, school):
        data = request.POST
        # data = {
        #     # 'member_email': data['member-email'],
        #     'member_school_email': data['member-school-email'],
        # }
        # print(data['member-school-email'])
        # mail_receiver = data.get('member_school_email')
        # mail_receiver = json.dump(data)

        # 메일 받는 것을 학교 메일로 받아준다.
        mail_receiver = school
        print(mail_receiver)

        # 0123456789 숫자중에 6자리를 랜덤으로 넘겨서 rn변수에 넣어준다.
        rn = ''.join(random.choices('0123456789', k=6))

        # 포트 번호를 587로 고정시켜준다.
        port = 587
        smtp_server = "smtp.gmail.com"
        # 보내는 사람 메일을 변수에 넣어준다.
        sender_email = "wmoon0024@gmail.com"

        # mail_receiver에 있는 값을 변수에 넣어준다.
        receiver_email = mail_receiver

        # 구글 1회성 비밀번호
        password = "pqxh ciic adcg numz"

        # 이메일 보낼때 쓰는 메세지
        message = f"<h1>인증번호 6자리 입니다 : {rn}</h1>"

        print("메일 들어옴")
        msg = MIMEText(message, 'html')
        data = MIMEMultipart()
        data.attach(msg)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            print("들어옴1")
            server.starttls(context=context)
            print("들어옴2")
            server.ehlo()
            print("들어옴3")
            server.login(sender_email, password)
            print("들어옴4")
            server.sendmail(sender_email, receiver_email, data.as_string())
            # print("들어옴5")
            # server.quit()
        # server.sendmail(sender_email, receiver_email, data.as_string())
        # uri = request.get_full_path()
        # request.session['previous_uri'] = uri
        # previous_page = request.META.get('HTTP_REFERER')
        # return render(previous_page)
        # return JsonResponse({'success': True, 'message': '성공!!!'})

class MemberIdSearchView(View):
    def get(self, request):
        return render(request, 'login/account-find.html')

class MemberActivateEmailView(APIView):
    def get(self,request):
        pass

    def post(self, request, email):
        # data = request.POST
        # data = {
        #     'member_email': data['member_email']
        # }

        members = Member.objects.all()
        member_email = Member.objects.get(member_email=email)
        member_id = member_email.id
        print(member_id)
        print("id 들어옴")
        # print(member_id)


        # 랜덤 숫자랑 문자열 10자리
        # 이메일 링크를 받으면 적어도 그 링크를 통해 접속이 된다.
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # 세션에 랜덤 코드 추가
        request.session['random_code'] = code
        # # 세션 저장
        # request.session.save()

        print(request.session['random_code'])

        # if member_email.exists():

        print(email)
        print(request.POST)
        # print(data['member-school-email'])
        mail_receiver = email
        # mail_receiver = json.dump(data)
        # mail_receiver = 'wmoon0024@gmail.com'
        print(mail_receiver)

        port = 587
        smtp_server = "smtp.gmail.com"
        sender_email = "wmoon0024@gmail.com"
        receiver_email = mail_receiver
        password = "pqxh ciic adcg numz"
        message = (f"<h1>비밀번호 계정 링크 입니다.</h1>\n"
                   f"<h2>http://127.0.0.1:10000/member/account-reset/{member_id}/{code}</h2>")

        print("메일 들어옴")
        msg = MIMEText(message, 'html')
        data = MIMEMultipart()
        data.attach(msg)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            print("들어옴1")
            server.starttls(context=context)
            print("들어옴2")
            server.ehlo()
            print("들어옴3")
            server.login(sender_email, password)
            print("들어옴4")
            server.sendmail(sender_email, receiver_email, data.as_string())

            return Response('fasjfksa')

# 비밀번호 변경 쪽
class MemberResetPasswordView(View):
    def get(self, request, id, random):
        # 메일로 링크를 받아 첫 회로 들어오고 나서 지워준다.
        # 링크를 다시 클릭했을 때 page not found가 뜬다.
        del request.session['random_code']

        # 맴버 id를 찾아서 변수에 넣어준다.
        member = Member.objects.get(id=id)

        # data 안에 맴버 아이디와 랜덤 받은 값을 넣어준다.
        data = {
            'id': member.id,
            'random': random
        }

        # if member.id == id:
        #     member.save(update_fields=['member_password'])
        # 수정된 정보가 있을 수 있기 때문에 세션 정보 최신화
        # request.session['member'] = MemberSerializer(Member.objects.get(id=request.session['member']['id'])).data
        # check = request.GET.get('check')
        # context = {'check': check}

        # 성공 했을시 render로 data값을 넘겨주어 다음 페이지로 넘겨준다.
        return render(request, 'login/reset-link.html', data)

    def post(self, request, id, random):
        data = request.POST

        # data 안에 맴버 아이디와 맴버 패스워드를 받는다.
        data = {

            'member_id': data['member-id'],
            'member_password': data['member-password'],
        }

        # 맴버 아이디를 받아 member 변수에 넣어준다.
        member = Member.objects.get(id=id)

        # 맴버 테이블에 패스워드 값을 받아 변수에 넣어준다.
        member.member_password = data['member_password']

        # 패스워드를 업데이트 쿼리를 써서 업데이트 시켜준다.
        member.save(update_fields=['member_password'])

        # 성공하면 로그인 페이지로 넘겨준다.
        return render(request, 'login/login.html')


class MemberMainView(View):
    def get(self, request):
        # member_name = request.session.get('member_name')

        # 맴버 테이블에 있는 맴버 id를 받아온 객체를 시리얼라이즈하여 JSON 형식으로 변환한다.
        # 객체를 맴버 이름에 있는 색션에 넣어준다.
        request.session['member_name'] = MemberSerializer(Member.objects.get(id=request.session['member']['id'])).data

        # 맴버 id에 있는 색션을 member 변수에 넣어준다.
        member = request.session['member']['id']

        # 맴버id와 위에 있는 member를 필터링 하여 첫번쨰 것을 profile 변수에 넣어준다.
        profile = MemberFile.objects.filter(member_id=member).first()

        # default_profile_url 에 기본 이미지를 넣어준다.
        default_profile_url = 'https://static.wadiz.kr/assets/icon/profile-icon-1.png'

        # 프로필이 아무것도 없으면
        if profile is None :

            # 기본 이미지 생성
            profile = default_profile_url

            # context 안에 profile 넣어준다.
            context = {
                'profile' : profile
            }

            # render로 context 받은 것을 메인 페이지에 넘겨준다.
            return render(request, 'main/main-page.html', context)

        # 프로필이 있으면
        else :
            # context 안에 profile을 넣어준다.
            context = {
                'profile': profile
            }

            # render로 context 받은 것을 메인 페이지에 넘겨준다.
            return render(request, 'main/main-page.html',context)



# 관리자 VIEW

class AdminMemberLoginView(View):
    def get(self, request):
        return render(request, 'admin/login.html')

    def post(self, request):
        data = request.POST
        data = {
            'member_email': data['member-email'],
            'member_password': data['member-password'],
        }

        # exists() 를 사용하기 위해서 QuerySet 객체로 조회
        member = Member.objects.filter(**data)
        url = 'member:admin_login'
        if member.exists():
            # 성공
            request.session['member'] = MemberSerializer(member.first()).data
            return redirect('member:admin_main')
        # 일괄처리한 것임.
        return redirect(url)

class AdminMainView(View):
    def get(self, request):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        visit_records = VisitRecord.objects.filter(date__range=[seven_days_ago, today])
        today_records = VisitRecord.objects.get(date = today)

        visit_records_total = VisitRecord.objects.filter(date__range=[seven_days_ago, today]).aggregate(total=Sum('count'))
        total_count = visit_records_total['total'] if visit_records_total['total'] is not None else 0

        # 각 visit_records의 date 필드를 문자열로 변환하여 직렬화
        visit_records_data = [{'date': record.date.strftime('%Y-%m-%d'), 'count': record.count} for record in
                              visit_records]
        visit_records_json = json.dumps(visit_records_data)

        context = {
            'visit_records_json': visit_records_json,
            'today_records': today_records,
            'visit_records_total': total_count
        }

        return render(request, 'admin/main.html', context)

class AdminMainUserView(View):
    def get(self, request):
        return render(request, 'admin/main_user.html')



class AdminMainUserListAPI(APIView):
    def get(self, request, page):
        row_count = 5
        offset = (page -1) * row_count
        limit = page * row_count

        columns = [
            'id',
            'member_email',
            'member_name',
            'member_phone',
            'created_date'
        ]

        keyword = request.GET.get('keyword', '')
        condition = Q()
        condition |= Q(member_name__icontains=keyword)

        members = Member.objects.filter(condition).values(*columns)[offset:limit]
        total_count = Member.objects.count()
        university_member_ids = list(University.objects.values_list('member', flat=True))
        school_members = School.objects.values_list('member', 'school_member_status')

        for member in members:
            member.setdefault('member-type', '일반회원')
            for school_member in school_members:
                if member['id'] == school_member[0]:
                    if school_member[1] == 0:
                        member['member-type'] = '학교 승인대기중'
                    elif school_member[1] == 1:
                        member['member-type'] = '학교회원'
                    break
                elif member['id'] in university_member_ids:
                    member['member-type'] = '대학생회원'

        member_info = {
            'members' : members,
            'total_count' : total_count,

        }

        return Response(member_info)

def translate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_items = data.get("selected_items")
        print(selected_items)

        for item_id in selected_items:
            try:
                School.objects.filter(member=item_id).update(school_member_status=True)

            except School.DoesNotExist:
                pass  # 항목이 존재하지 않는 경우 무시

        return JsonResponse({'message': '선택된 항목이 성공적으로 전환되었습니다.'})

    return JsonResponse({'error': 'POST 요청이 필요합니다.'}, status=400)

class AdminMainNotificationView(View):
    def get(self, request):
        return render(request, 'admin/main_notification.html')


class AdminNotificationListAPI(APIView):
    def get(self, request, page):
        row_count = 5
        offset = (page - 1) * row_count
        limit = page * row_count

        columns = [
            'id',
            'notification_title',
            'notification_status',
            'created_date',
            'notification_view_count'
        ]

        option = request.GET.get('option')

        if option == '커뮤니티':
            notifications = Notification.enabled_objects.filter(notification_status=0).values(*columns)[offset:limit]
            total_count = Notification.enabled_objects.filter(notification_status=0).count()
        elif option == '원랩':
            notifications = Notification.enabled_objects.filter(notification_status=1).values(*columns)[offset:limit]
            total_count = Notification.enabled_objects.filter(notification_status=1).count()
        elif option == '장소공유':
            notifications = Notification.enabled_objects.filter(notification_status=2).values(*columns)[offset:limit]
            total_count = Notification.enabled_objects.filter(notification_status=2).count()
        elif option == '공모전':
            notifications = Notification.enabled_objects.filter(notification_status=3).values(*columns)[offset:limit]
            total_count = Notification.enabled_objects.filter(notification_status=3).count()
        else:
            notifications = Notification.enabled_objects.values(*columns)[offset:limit]
            total_count = Notification.enabled_objects.count()



        notification_info= {
            'notifications' : notifications,
            'total_count' : total_count
        }

        return Response(notification_info)

def soft_delete(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_items = data.get("selected_items")
        print(selected_items)
        # 선택된 항목들의 상태를 0으로 변경하는 코드 작성
        for item_id in selected_items:
            try:
                Notification.objects.filter(id=item_id).update(notification_post_status=False)

            except Notification.DoesNotExist:
                pass  # 항목이 존재하지 않는 경우 무시

        return JsonResponse({'message': '선택된 항목이 성공적으로 삭제되었습니다.'})

    return JsonResponse({'error': 'POST 요청이 필요합니다.'}, status=400)


class AdminMainExhibitionView(View):
    def get(self, request):
        return render(request, 'admin/main_exhibition.html')


class AdminMainExhibitionListAPI(APIView):
    def get(self, request, page):
        row_count = 5
        offset = (page -1) * row_count
        limit = page * row_count

        columns = [
            'id',
            'exhibition_title',
            'exhibition_view_count',
            'school__member__member_name',
            'created_date'
        ]

        exhibitions = Exhibition.enabled_objects\
                          .annotate(school_member_name=F('school__member__member_name')).values(*columns)[offset:limit]
        total_count = Exhibition.enabled_objects.count()
        exhibition_info = {
            'exhibitions' : exhibitions,
            'total_count' : total_count
        }

        return Response(exhibition_info)

def soft_delete_exhibition(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_items = data.get("selected_items")
        print(selected_items)
        # 선택된 항목들의 상태를 0으로 변경하는 코드 작성
        for item_id in selected_items:
            try:
                Exhibition.objects.filter(id=item_id).update(exhibition_post_status=False)

            except Exhibition.DoesNotExist:
                pass  # 항목이 존재하지 않는 경우 무시

        return JsonResponse({'message': '선택된 항목이 성공적으로 삭제되었습니다.'})

    return JsonResponse({'error': 'POST 요청이 필요합니다.'}, status=400)


class AdminMainLogoutView(View):
    def get(self, request):
        request.session.clear()
        return redirect('/')
