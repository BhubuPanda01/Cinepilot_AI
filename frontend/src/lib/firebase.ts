import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Analytics is intentionally omitted -- it requires a browser-only measurement
// API that doesn't play well with Next.js server rendering, and isn't needed
// for auth/Firestore functionality.
const firebaseConfig = {
  apiKey: "AIzaSyBESHfHjVwL9l2jNdHRrr1NnVgpGvCXSx0",
  authDomain: "cinepilotai.firebaseapp.com",
  projectId: "cinepilotai",
  storageBucket: "cinepilotai.firebasestorage.app",
  messagingSenderId: "697076662578",
  appId: "1:697076662578:web:5ecc4ed6ec45ed1ed2572b",
};

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
