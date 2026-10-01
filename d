특정 서브 명령어에 대해 읽고 싶다면 'git help <command>'를 보시오

주요 사용자용 명령
   add                  파일 내용을 인덱스에 추가합니다
   am                   메일함에서 연속된 패치를 적용합니다
   archive              지정한 트리에 들어 있는 파일의 아카이브를 만듭니다
   bisect               이진 탐색으로 버그를 만들어낸 커밋을 찾습니다
   branch               브랜치를 만들거나, 삭제하거나, 목록을 출력합니다
   bundle               아카이브 형태로 오브젝트와 레퍼런스를 옮깁니다
   checkout             브랜치를 전환하거나 작업 파일을 복구합니다
   cherry-pick          기존 커밋으로 발생한 변경 사항을 적용합니다
   citool               git-commit의 그래픽 대체 버전
   clean                작업 폴더에서 추적되지 않는 파일을 제거합니다
   clone                저장소를 복제해 새 디렉터리로 가져옵니다
   commit               바뀐 사항을 저장소에 기록합니다
   describe             사용 가능한 레퍼런스를 기준으로 오브젝트에 읽을 수 있는 이름을 부여합니다
   diff                 커밋과 커밋 사이, 커밋과 작업 내용 사이 등의 바뀐 점을 봅니다
   fetch                다른 저장소에서 오브젝트와 레퍼런스를 다운로드합니다
   format-patch         메일 제출 용도로 패치를 준비합니다
   gc                   불필요한 파일을 지우고 로컬 저장소를 최적화합니다
   gitk                 깃 저장소 살펴보기
   grep                 패턴과 일치하는 줄을 표시합니다
   gui                  깃의 포터블 그래픽 인터페이스
   init                 빈 깃 저장소를 만들거나 기존 저장소를 다시 초기화합니다
   log                  커밋 기록을 표시합니다
   maintenance          Run tasks to optimize Git repository data
   merge                여러 개의 개발 내역을 하나로 합칩니다
   mv                   파일, 디렉터리, 심볼릭 링크를 옮기거나 이름을 바꿉니다
   notes                오브젝트 노트를 추가하거나 살펴봅니다
   pull                 다른 저장소 또는 다른 로컬 브랜치에서 가져오거나 통합합니다
   push                 원격 레퍼런스 및 그와 관련된 오브젝트를 업데이트합니다
   range-diff           Compare two commit ranges (e.g. two versions of a branch)
   rebase               커밋을 다른 베이스 끝의 최상위에서 적용합니다
   reset                현재 HEAD를 지정한 상태로 재설정화합니다
   restore              작업트리 파일을 복구합니다
   revert               기존 커밋을 되돌립니다
   rm                   파일을 작업 폴더에서 제거하고 인덱스에서도 제거합니다
   shortlog             'git log' 출력을 요약합니다
   show                 여러가지 종류의 오브젝트를 표시합니다
   sparse-checkout      Initialize and modify the sparse-checkout
   stash                작업 폴더의 변경 사항을 임시로 다른 곳에 저장합니다
   status               작업 폴더 상태를 표시합니다
   submodule            하위 모듈을 초기화하거나, 업데이트하거나, 조사합니다
   switch               브랜치를 이동합니다
   tag                  태그를 만들거나, 표시하거나, 삭제하거나, GPG 서명을 검증합니다
   worktree             여러 개의 작업 폴더를 관리합니다

보조 명령 / 조작 기능
   config               저장소 옵션 또는 전체 옵션을 보거나 설정합니다
   fast-export          깃 데이터 내보내기
   fast-import          고속 깃 데이터 가져오기 백엔드
   filter-branch        리모트 브랜치
   mergetool            병합 충돌 상황에서 병합 충돌 해결 도구를 실행합니다
   pack-refs            효율적인 저장소 접근을 위해 헤드와 태그를 묶습니다
   prune                오브젝트 데이터베이스에서 도달할 수 없는 오브젝트를 모두 잘라냅니다
   reflog               reflog 정보를 관리합니다
   remote               추적하는 저장소 모음을 관리합니다
   repack               저장소의 묶여지지 않은 오브젝트를 묶습니다
   replace              오브젝트를 바꾸는 레퍼런스를 만들거나, 표시하거나, 삭제합니다

보조 명령 / 정보 획득 기능
   annotate             파일 줄마다 커밋 정보를 표시합니다
   blame                파일 줄마다 끝에 마지막으로 수정한 리비전과 작성자를 표시합니다
   bugreport            Collect information for user to file a bug report
   count-objects        묶여지지 않은 오브젝트의 개수 및 그 디스크 사용량을 측정합니다
   difftool             일반적인 diff 도구를 사용해 변경 사항을 표시합니다
   fsck                 연결을 확인하고 데이터베이스의 오브젝트가 올바른지 확인합니다
   gitweb               깃 웹 인터페이스 (깃 저장소에 대한 웹 프론트엔드)
   help                 깃의 도움말 정보를 표시합니다
   instaweb             내 작업 저장소를 gitweb에서 즉시 살펴봅니다
   merge-tree           인덱스를 바꾸지 않고 3-방향 병합을 표시합니다
   rerere               충돌하는 병합의 기록된 해결 방법을 다시 사용합니다
   show-branch          브랜치 목록과 그 커밋을 표시합니다
   verify-commit        커밋의 GPG 서명을 확인합니다
   verify-tag           태그의 GPG 서명을 확인합니다
   whatchanged          각 커밋으로 발생하는 차이점마다 기록을 표시합니다

다른 사람과 소통
   archimport           Import a GNU Arch repository into Git
   cvsexportcommit      하나의 커밋을 CVS 체크아웃으로 내보냅니다
   cvsimport            다른 소스 코드 관리 시스템에서 데이터 가져오기
   cvsserver            깃용 CVS 서버 에뮬레이터
   imap-send            표준입력에서 패치 모음을 읽어 IMAP 폴더로 보냅니다
   p4                   Perforce 저장소에서 가져오거나 저장소로 제출합니다
   quiltimport          현재 브랜치에 quilt 패치 모음을 적용합니다
   request-pull         예정된 변경 사항의 요약을 만듭니다
   send-email           패치 모음을 메일로 보냅니다
   svn                  서브버전 저장소와 깃 사이의 양방향 동작

저수준 명령/ 조작 기능
   apply                패치를 파일 및/또는 인덱스에 적용합니다
   checkout-index       인덱스의 파일을 작업 폴더로 복사합니다
   commit-graph         Write and verify Git commit-graph files
   commit-tree          새 커밋 오브젝트를 만듭니다
   hash-object          오브젝트 ID를 계산하고 선택적으로 파일의 블롭을 만듭니다
   index-pack           기존 묶음 아카이브에 대한 묶음 인덱스 파일을 만듭니다
   merge-file           3-방향 파일 병합을 실행합니다
   merge-index          병합이 필요한 파일에 대해 병합을 실행합니다
   mktag                Creates a tag object with extra validation
   mktree               ls-tree 포맷의 텍스트에서 tree-object를 만듭니다
   multi-pack-index     Write and verify multi-pack-indexes
   pack-objects         오브젝트의 묶음 아카이브를 만듭니다
   prune-packed         묶음 파일에 이미 들어 있는 오브젝트를 추가로 제거합니다
   read-tree            트리 정보를 인덱스로 읽습니다
   symbolic-ref         심볼릭 레퍼런스를 읽고, 수정하고, 삭제합니다
   unpack-objects       묶음 아카이브에서 오브젝트를 풀어냅니다
   update-index         작업 폴더에서 파일 내용을 인덱스에 등록합니다
   update-ref           레퍼런스에 저장된 오브젝트 이름을 안전하게 업데이트합니다
   write-tree           현재 인덱스에서 트리 오브젝트를 만듭니다

보조 명령 / 정보 획득 기능
   cat-file             저장소 오브젝트에 대해 내용 또는 종류와 크기 정보를 표시합니다
   cherry               업스트림에 적용해야 할 커밋을 찾습니다
   diff-files           작업 폴더와 인덱스의 파일을 비교합니다
   diff-index           트리를 작업 폴더나 인덱스와 비교합니다
   diff-tree            두 개의 트리 오브젝트에 있는 내용과 블롭의 모드를 비교합니다
   for-each-ref         각 레퍼런스의 정보를 출력합니다
   for-each-repo        Run a Git command on a list of repositories
   get-tar-commit-id    git-archive로 만든 아카이브에서 커밋 ID를 추출합니다
   ls-files             인덱스와 작업 폴더의 파일에 대한 정보를 표시합니다
   ls-remote            원격 저장소의 레퍼런스를 열거합니다
   ls-tree              트리 오브젝트의 내용을 열거합니다
   merge-base           병합에 사용할 최선의 공통 과거 커밋을 찾습니다
   name-rev             주어진 리비전에 대한 심볼 이름을 찾습니다
   pack-redundant       중복된 묶음 파일을 찾습니다
   rev-list             시간 반대 순서에 따라 커밋 오브젝트를 열거합니다
   rev-parse            파라미터를 찾아내서 조정합니다
   show-index           묶여진 아카이브 인덱스를 표시합니다
   show-ref             로컬 저장소의 레퍼런스를 열거합니다
   unpack-file          블롭의 내용으로 임시 파일을 만듭니다
   var                  깃의 논리적 변수를 표시합니다
   verify-pack          묶음 깃 아카이브 파일을 검증합니다

Low-level Commands / Syncing Repositories
   daemon               깃 저장소에 대한 아주 간단한 서버
   fetch-pack           다른 저장소에서 없는 오브젝트를 다운로드합니다
   http-backend         깃 HTTP 프로토콜의 서버측 구현
   send-pack            오브젝트를 깃 프로토콜을 통해 다른 저장소로 푸시합니다
   update-server-info   단순 서버에 도움을 주도록 보조 정보 파일을 업데이트합니다

보조 명령 / 내부 사용 기능
   check-attr           gitattributes 정보를 표시합니다
   check-ignore         gitignore / 제외할 파일을 디버깅합니다
   check-mailmap        연락처의 전체 이름과 메일 주소를 표시합니다
   check-ref-format     레퍼런스 이름의 형식이 올바른지 확인합니다
   column               데이터를 여러 열로 표시합니다
   credential           사용자 비밀 정보를 가져오고 저장합니다
   credential-cache     메모리에 임시로 암호 저장하는 도움 명령
   credential-store     비밀 정보를 디스크에 저장하는 도움 명령
   fmt-merge-msg        병합 커밋 메시지를 만듭니다
   interpret-trailers   Add or parse structured information in commit messages
   mailinfo             하나의 메일 메시지에서 패치와 작성자 정보를 뽑아냅니다
   mailsplit            간단한 유닉스 mbox 쪼개기 프로그램
   merge-one-file       git-merge-index와 같이 사용하는 기본 도움 프로그램
   patch-id             패치에 대한 유일한 ID를 계산합니다
   sh-i18n              셸 스크립트를 위한 깃의 국제화 준비 코드
   sh-setup             공통 깃 셸 스크립트 준비 코드
   stripspace           불필요한 공백 문자를 제거합니다

외부 명령어
   bloom-branch
   bloom-config
   bloom-generate
   bloom-import-upstream
   bloom-patch
   bloom-release
   filter-repo
   lfs
