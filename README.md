# PREPARE
```bash
# pip3 install Flask
# pip3 install PyMySQL
```

# DATABASE SETTINGS
...

# ACTIVATE SERVER
```base
$ sudo /etc/init.d/mysql start
$ sudo python3 operator.py
```

# TESTCASE
## 1. user authorization request

(user -> data-source)

```bash
$ curl -X GET {{data-source IP}}/authorize?response_type=authorization_code&scope={{1}}&operator_id=operator_id_001&redirect_uri=http://operator.example.com/cb&state={{2}}
```

{{1}}: banking / medical / public 중 택1

{{2}}: user가 operator에 가입한 id명

## 2. access token request

(operator -> data-source)

```bash
curl -X POST {{data-source IP}}/token -d "grant_type=authorization_code&code={{grant_code}}&redirect_uri=http://operator.example.com/cb" -H "Authorization: Basic b3BlcmF0b3JfaWRfMDAxOnB3X29wZXJhdG9y" -H "Content-Type: application/x-www-form-urlencoded"
```

## 3. Accessing Protected Resources

(operator -> data-source)

```bash
curl -X GET {{data-source IP}}/resource?token={{access_token}}
```