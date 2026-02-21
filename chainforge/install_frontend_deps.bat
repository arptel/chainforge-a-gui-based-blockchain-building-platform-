@echo off
cd chainforge/platform-frontend
echo Installing dependencies...
npm install
echo Installing dev dependencies...
npm install -D tailwindcss postcss autoprefixer
echo Installing UI dependencies...
npm install class-variance-authority clsx tailwind-merge lucide-react framer-motion axios zustand
npm install @radix-ui/react-slot @radix-ui/react-label @radix-ui/react-select @radix-ui/react-dialog @radix-ui/react-separator @radix-ui/react-tabs
echo Done!
pause
