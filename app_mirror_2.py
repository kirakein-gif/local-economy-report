# 미러 앱 전용 진입 파일입니다. 실제 코드는 전부 local_economy_report.py에 있고,
# 이 파일은 그걸 그대로 실행만 합니다. 로직을 고칠 땐 local_economy_report.py만
# 고치면 이 파일도 자동으로 최신 내용으로 동작합니다.
exec(open("local_economy_report.py", encoding="utf-8").read())
