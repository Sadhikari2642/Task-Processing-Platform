import React, { useState } from 'react'
import API from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function Login(){
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const nav = useNavigate();
  const submit = async e => {
    e.preventDefault();
    const r = await API.post('/auth/login',{ email, password });
    localStorage.setItem('token', r.data.token);
    API.defaults.headers.common['Authorization'] = 'Bearer '+r.data.token;
    nav('/dashboard');
  };
  return (
    <form onSubmit={submit}>
      <input value={email} onChange={e=>setEmail(e.target.value)} placeholder="email" />
      <input value={password} onChange={e=>setPassword(e.target.value)} placeholder="password" type="password" />
      <button>Login</button>
    </form>
  )
}
