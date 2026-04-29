import React, { useEffect, useState } from 'react'
import API from '../services/api'

export default function Dashboard(){
  const [tasks, setTasks] = useState([]);
  const [form, setForm] = useState({title:'', inputText:'', operation:'uppercase'});
  useEffect(()=>{ API.get('/tasks').then(r=>setTasks(r.data)).catch(()=>{}); },[]);
  const submit = async e => { e.preventDefault(); await API.post('/tasks', form); const r = await API.get('/tasks'); setTasks(r.data); }
  return (
    <div>
      <h3>Create Task</h3>
      <form onSubmit={submit}>
        <input placeholder="title" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} />
        <input placeholder="inputText" value={form.inputText} onChange={e=>setForm({...form,inputText:e.target.value})} />
        <select value={form.operation} onChange={e=>setForm({...form,operation:e.target.value})}>
          <option>uppercase</option>
          <option>lowercase</option>
          <option>reverse</option>
          <option>wordcount</option>
        </select>
        <button>Create</button>
      </form>
      <h3>Tasks</h3>
      <ul>{tasks.map(t=> <li key={t._id}>{t.title} - {t.status} - {JSON.stringify(t.result)}</li>)}</ul>
    </div>
  )
}
