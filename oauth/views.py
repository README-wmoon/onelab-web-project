from allauth.socialaccount.models import SocialAccount
from django.views import View
from django.shortcuts import render, redirect

from member.models import Member
from member.serializers import MemberSerializer


class OAuthLoginView(View):
    def get(self, request):
        # SocialAccount(카카오, 네이버, 구글)에 있는 user을 요청해서 get으로 받는다.
        user = SocialAccount.objects.get(user=request.user)

        # 다른 데이터에 추가시킬것을 변수에 넣어준다.
        oauth_data = user.extra_data
        # 카카오 유저일때
        if user.provider == "kakao":
            # 카카오 account에 있는 이메일을 변수에 넣어준다.
            member_email = oauth_data.get("kakao_account").get("email")
            # 카카오 account에 있는 이름을 변수에 넣어준다.
            member_nickname = oauth_data.get("properties").get("nickname")

            # 카카오 account에 있는 프로필 이미지를 변수에 넣어준다.
            member_profile_image = oauth_data.get("properties").get("profile_image")
        # 카카오 유저가 아니면
        else:
            # 직접적으로 이메일을 받은 것을 변수에 넘겨준다.
            member_email = oauth_data.get("email")
            # 직접적으로 이름을 받은 것을 변수에 넘겨준다.
            member_nickname = oauth_data.get("name")

            # 직접적으로 phone에 받은 것을 변수에 넘겨준다.
            member_phone = oauth_data.get("phone")

            # 직접적으로 picture에 받은 것을 변수에 넘겨준다.
            member_profile_image = oauth_data.get("picture")

        # data 안에 맴버 이메일과 이름을 받는다.
        data = {
            'member_email': member_email,
            'member_name': member_nickname,
            # 'member_profile_image': member_profile_image,
        }
        # member = Member.objects.filter(member_email=data['member_email'])
        # 최초 로그인 검사
        # 카카오,네이버,구글 최조 로그인시 OAuth에서 받은 이메일과 이름을 추가시켜준다.
        member, created = Member.objects \
            .get_or_create(member_email=member_email, member_type=user.provider, member_name=member_nickname)

        url = '/'


        # if member.exists():
        #     request.session['member'] = MemberSerializer(member.first()).data
        # else:
        #     request.session['join-member-data'] = data
        #     url = "member:join"



        # 최초 로그인(회원가입 필요)
        # 반드시 입력받아야 되는 것을 써야된다.
        # url 변수를 'main'으로 초기화
        url = "main"
        # 회원 이름이 없거나 새로 생성된 회원인 경우
        if member.member_name is None or created:
            # return redirect(f'/?member=_email={member_email}&member_type={user.provider}&id={member.id}')
            # 맴버 이메일,타입 provider, id, member_name을 변수에 넣어준다.
            url = f'/member/join/?member_email={member_email}&member_type={user.provider}&id={member.id}&member_name={member.member_name}'

        # OAuth 최초 로그인이 아닐 경우 조회된 member 객체를 세션에 담아준다.
        request.session['member'] = MemberSerializer(member).data

        # redirect 써서 url에 있는 데이터를 넘겨준다.
        return redirect(url)