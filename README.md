# 2026_study
  |- /huduby/   내꺼   작업폴더   
  |- /iseee/    양호샘 작업폴더

  * 각 폴더 아래에 프로젝트 폴더를 생성해서 각 프로젝트 별로 소스 분리  

## git 명령어 사용하기
1. 로컬 컴퓨터의 working 디렉토리를 만들 위치로 cmd 경로 옮기기 ( 예 : d:\> )
2. d:\\> git clone https://github.com/huduby777/2026_study.git  
      ***<b>\2026_study\huduby\  </b>***   
      ***<b>\2026_study\isee\  </b>*** 
       기존에 원격지 github 에 있던 파일을 로컬로 다운로드 완료 ( clone 함 )
3. \2026_study\huduby\프로젝트명> working 디렉토리 작업  
4.  소스 작업 후
   \2026_study> **git pull origin main**       # 다른 사람이 작업한 내역 모두 가져와서 로컬=원격 맞추기
   \2026_study> **git add .**                  # 작업한 모든 소스 git 저장소에 등록  
   \2026_study> **git commit -m "커밋메세지"**  # 등록된 소스를 저장소에 저장  
   \2026_study> **git push origin main**       # git 저장소에 저장된 소스 내역을 github 원격지에 push
5. git push 전에 확인
   \2026_study> **git branch**                 # branch 명에 *main 이 있어야 함.  
   \2026_study> **git branch -M main**         # *master 이나 기타 다른 branch라면 main으로 바꾸어줘야 함.

6. 추가 작업 후  
   git pull 시 아래와 같은 오류가 발생하는 경우 --> git pull origin main --allow-unrelated-histories --no-rebase 실행  
   <img width="536" height="108" alt="image" src="https://github.com/user-attachments/assets/1bc8c6a1-7ab5-4e5c-96ad-ca011c0a2cf5" />  

     
