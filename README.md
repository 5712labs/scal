# Tutorials
## ⚙️ Installation
* **프로젝트를 원하는 폴더에 생성하세요**
```shell script
git clone https://github.com/5712labs/scal.git
```
* **[VSCode](https://code.visualstudio.com) 등의 편집기로 프로젝트 폴더를 열어주세요** 
* **터미널을 실행하여 패키지를 설치하세요**
```shell script
pip install -r requirements.txt
```
* **사용하실 API키 파일을 생성하세요**
```toml
#PATH /.streamlit/secrets.toml
[필수API]
api_dw = "챗GPT_API_KEY"
api_deepl = "DEEPL번역_API_KEY"
api_youtube = "YOUTUBE검색_API_KEY"

[선택]
dwenc_auth  = "AUTH 인증용 주소"
dwenc_token = "AUTH 인증용 토큰"
dwenc_sso   = "SSO 접속주소"
dwenc_user  = "SSO USER"
dwenc_pass  = "SSO PASS"
```
* **Local 실행 시 임시사용자 정보 json 파일을 생성하세요**
```json
#PATH /db/local_user.json
{
  "userNm": "정대우", 
  "orgNm": "우리팀", 
  "orgCd": "1TEAM", 
  "userId": "1234567", 
  "email": "dwenc@dwenc.com"
}
```
## 🛠️ (Optional) Installation
* **SAP 연동은** [PyRFC](https://github.com/SAP/PyRFC) **에서 패키지를 별도로 설치해야합니다.**
* **SAP 접속정보 json 파일을 생성하세요**
```json
#PATH /db/sap_connect_dcd.json (개발)
      /db/sap_connect_dcp.json (운영)
{
    "ashost": "111.22.3.44",
    "sysnr" : "00",
    "client" : "111",
    "user" : "user_id",
    "passwd" : "passwd"
}
```
## ⚡ Quickstart
```shell script
streamlit run Home.py
```
* **실행 후 [http://localhost:8501](http://localhost:8501) 접속하세요**

## More...
* **[PM2 (Process Management)](https://pm2.keymetrics.io)** **무중단 서비스를 구현해보세요.**
```python
#PATH run_Home.py
import subprocess
subprocess.run(["streamlit", "run", "Home.py"])
```

```shell script
pm2 start run_Home.py
pm2 list
pm2 status
pm2 monit
pm2 kill
```

## Todo
- Docker
- ~~SSL~~
- ~~SSO~~
- MongoDB

