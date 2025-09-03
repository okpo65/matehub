#!/bin/bash

echo "🚀 MateHub Frontend 서버 시작..."
echo "📍 http://localhost:3000 에서 접속 가능합니다"
echo "🔐 로그인 페이지: http://localhost:3000/auth.html"
echo "💬 채팅 페이지: http://localhost:3000/index.html"
echo ""
echo "⚠️  백엔드 서버가 http://localhost:8000 에서 실행 중인지 확인하세요"
echo ""

# Python 서버로 실행
python3 -m http.server 3000
