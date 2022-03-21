# Mydata System - Operator

## PREPARE
```bash
$ sudo apt install mysql-server
$ sudo apt install python3-pip
$ sudo pip3 install Flask
$ sudo pip3 install PyMySQL
$ sudo pip3 install flask-mysql
$ sudo pip3 install requests
# https://askubuntu.com/questions/1261775/why-cant-i-install-python-3-8
```

## DATABASE SETTINGS
```sql
> create database operator;
> create user operator@localhost identified by 'mysql_pw';
> grant all on operator.* to operator@localhost;
```

## ACTIVATE SERVER
```bash
$ sudo /etc/init.d/mysql start
~/operator $ git pull           # update files from github
~/operator $ sudo python3 operator.py
```

## Usage

### For User Device

1. <b>sign_up</b> : mydata system을 이용할 user를 등록
   - 접속 url: `/signup` (POST request)
   - parameters
     - `id` : 등록할 새 user의 id
     - `password` : 등록할 새 user의 password
   - <b>sign up 성공시</b> : `"sign up success\n"` 반환
   - <b>sign up 실패시</b> : -
2. <b>register</b> : user의 데이터를 operator에 등록
   - 접속 url: `/register` (POST request, GET 인자도 사용)
   - POST parameters
     - `id` : user의  id
     - `password` : user의 password
   - GET parameters
     - `scope` : 등록하고자 하는 데이터의 종류 ('financial_data', 'public_data', 'medical_data' 중 택1)
   - <b>register 성공시</b> : redirect response 반환
   - <b>id/password 미일치시</b> : `"[ERROR] wrong id or password\n"` 반환
   - <b>parameter 누락시</b> : `"[ERROR] <parameter명> required\n"` 반환
3. <b>get data</b> : 등록된 user의 데이터를 열람
   - 접속 url: `/data` (POST request, GET 인자도 사용)
   - POST parameters
     - `id` : user의  id
     - `password` : user의 password
   - GET parameters
     - `scope` : 등록하고자 하는 데이터의 종류 ('financial_data', 'public_data', 'medical_data' 중 택1)
   - <b>열람 성공시</b> : user의 data를 json 형태로 반환
   - <b>id/password 미일치시</b> : `"[ERROR] wrong id or password\n"` 반환
   - <b>parameter 누락시</b> : `"[ERROR] <parameter명> required\n"` 반환
4. <b>refresh</b> : user의 데이터를 data-source로 부터 다시 불러옴
   - 접속 url: `/refresh` (POST request, GET 인자도 사용)
   - POST parameters
     - `id `: user의  id
     - `password` : user의 password
   - GET parameters
     - `scope `: 등록하고자 하는 데이터의 종류 ('financial_data', 'public_data', 'medical_data' 중 택1)
   - <b>refresh 성공시</b> : `"success\n"` 반환
   - <b>id/password 미일치시</b> : `"[ERROR] wrong id or password\n"` 반환
   - <b>parameter 누락시</b> : `"[ERROR] <parameter명> required\n"` 반환
5. <b>delete</b> : 등록된 user의 데이터를 operator에서 등록 해제 및 삭제

   - 접속 url: `/delete` (POST request, GET 인자도 사용)
   - POST parameters
     - `id `: user의  id
     - `password` : user의 password
   - GET parameters
     - `scope` : 등록하고자 하는 데이터의 종류 ('financial_data', 'public_data', 'medical_data' 중 택1)
   - <b>delete 성공시</b> : `"success\n"` 반환
   - <b>id/password 미일치시</b> : `"[ERROR] wrong id or password\n"` 반환
   - <b>parameter 누락시</b> : `"[ERROR] <parameter명> required\n"` 반환
6. <b>callback</b> : user로 부터 grant code를 받아 data-source에게 제출한 뒤 access token 획득, 그 후 data 등록 까지 진행
   - 접속 url: `/cb` (user가 직접 해당 url에 접속할 필요는 없으며 register 과정 후 자동적으로 접속하게 됨)
   - <b>data 등록 성공시</b> : `"success\n"` 반환
   - <b>parameter 누락시</b> : `"[ERROR] <parameter명> required\n"` 반환 -> 이 경우 data-source 측 소스 수정 필요
   - <b>register 과정을 거치지 않고 의도적으로 `/cb`에 진입한 경우</b> : `"[ERROR] Not Proper Access\n"` 반환

## TESTCASE
### 1. user authorization request

(user -> data-source)

```bash
$ curl -X GET {{data-source IP}}/authorize?response_type=authorization_code&scope={{1}}&operator_id=operator_id_001&redirect_uri=http://operator.example.com/cb&state={{2}}
```

{{1}}: banking / medical / public 중 택1

{{2}}: user가 operator에 가입한 id명

### 2. access token request

(operator -> data-source)

```bash
$ curl -X POST {{data-source IP}}/token -d "grant_type=authorization_code&code={{grant_code}}&redirect_uri=http://operator.example.com/cb" -H "Authorization: Basic b3BlcmF0b3JfaWRfMDAxOnB3X29wZXJhdG9y" -H "Content-Type: application/x-www-form-urlencoded"
```

### 3. Accessing Protected Resources

(operator -> data-source)

```bash
$ curl -X GET {{data-source IP}}/resource?token={{access_token}}
```