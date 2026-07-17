import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { getMessaging } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js";

const firebaseConfig = {
  apiKey: "AIzaSyALBqEc_ZKvXCoi51uhtYyIJhoi_4rpptc",
  authDomain: "fallguard-family.firebaseapp.com",
  projectId: "fallguard-family",
  storageBucket: "fallguard-family.firebasestorage.app",
  messagingSenderId: "543935846728",
  appId: "1:543935846728:web:9bfe0c7e0e8da47f88bb7d"
};

export const VAPID_KEY = "BHsBwrPfVhdp7Pc0nVeNnqgA5CBTPxV0GpQOMYmNEef2qrapO2iq1TTWHBrjExLfRldoFdE67rp2HYpklKuFLHs";

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const messaging = getMessaging(app);


export const BACKEND_URL = "https://my-app-backend-xt03.onrender.com";
