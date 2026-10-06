# 2026_study
  |- /huduby/   내꺼   작업폴더   
  |- /iseee/    양호샘 작업폴더

  * 각 폴더 아래에 프로젝트 폴더를 생성해서 각 프로젝트 별로 소스 분리  

## git 명령어 사용하기
1. 로컬 컴퓨터의 working 디렉토리를 만들 위치로 cmd 경로 옮기기 ( 예 : d:\> )
2. d:\\...\\> git clone https://github.com/huduby777/2026_study.git  
      ***<b>d:\2026_study\huduby\  </b>***   
      ***<b>d:\2026_study\isee\  </b>*** 
       기존에 원격지 github 에 있던 파일을 로컬로 다운로드 완료 ( clone 함 )
3. d:\..\2026_study\huduby\프로젝트명> working 디렉토리 작업  
4. 모든 소스 작업 후
   d:\..\2026_study> **git add .**                  # 작업한 모든 소스 git 저장소에 등록  
   d:\..\2026_study> **git commit -m "커밋메세지"**  # 등록된 소스를 저장소에 저장  
   d:\..\2026_study> **git push origin main**       # git 저장소에 저장된 소스 내역을 github 원격지에 push
5. git push 전에 확인
   d:\..\2026_study> **git branch**                 # branch 명에 *main 이 있어야 함.  
   d:\..\2026_study> **git branch -M main**         # *master 이나 기타 다른 branch라면 main으로 바꾸어줘야 함.
     
