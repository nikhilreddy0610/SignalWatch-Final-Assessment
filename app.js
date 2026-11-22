const $=id=>document.getElementById(id);
let apiKey=sessionStorage.getItem('signalwatch_api_key')||'';
let sessionId=localStorage.getItem('signalwatch_session')||crypto.randomUUID();
localStorage.setItem('signalwatch_session',sessionId);
const statuses=['anticipated','active','evolving','resolved'];

async function api(path,options={}){
  const headers={'Content-Type':'application/json',...(apiKey?{'X-API-Key':apiKey}:{}),...(options.headers||{})};
  const response=await fetch(path,{...options,headers});
  if(!response.ok){let detail;try{detail=(await response.json()).detail}catch{detail=await response.text()}throw new Error(detail||`Request failed (${response.status})`)}
  return response.json();
}
function esc(value){return String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}
function safeUrl(value){try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)?url.href:''}catch{return ''}}
function showAccess(){ $('accessState').textContent=apiKey?'API key set for this tab':'API access open';$('sessionLabel').textContent=`Session ${sessionId.slice(0,8)}` }
function appendMessage(role,text,error=false){
  const bubble=document.createElement('div');bubble.className=`bubble ${role}${error?' error':''}`;bubble.textContent=text;$('chatlog').append(bubble);$('chatlog').scrollTop=$('chatlog').scrollHeight;return bubble;
}
function showSources(sources=[]){
  $('sources').replaceChildren();
  if(!sources.length)return;
  for(const source of sources){
    const card=document.createElement('div');card.className='source-card';
    const url=safeUrl(source.url);
    card.innerHTML=url?`[${esc(source.id)}] <a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(source.title||source.source||'Evidence source')}</a>`:`[${esc(source.id)}] ${esc(source.title||source.source||'Source')}`;
    $('sources').append(card);
  }
}
function renderThreats(items=[]){
  $('threats').innerHTML=items.length?items.map(item=>`<article class="threat-card">
    <div class="card-top"><span class="tag ${esc(item.status)}">${esc(item.status)}</span><span class="tag">${esc(item.platform)}</span>${item.severity?`<span class="tag">${esc(item.severity)}</span>`:''}${item.record_type==='demo_synthetic'?'<span class="tag">Synthetic demo</span>':''}</div>
    <h3>${esc(item.title)}</h3><p>${esc(item.summary)}</p>${item.cve?`<p><strong>Advisory:</strong> ${esc(item.cve)}</p>`:''}${item.mitigation?`<p><strong>Mitigation:</strong> ${esc(item.mitigation)}</p>`:''}
    ${safeUrl(item.source_url)?`<a class="text-link" href="${esc(safeUrl(item.source_url))}" target="_blank" rel="noopener noreferrer">Open evidence source ↗</a>`:''}
    <div class="card-actions"><button class="button secondary" data-edit-threat="${esc(item.id)}">Edit</button><button class="button secondary" data-delete-threat="${esc(item.id)}">Delete</button></div>
  </article>`).join(''):'<p class="empty-state">No matching records yet. Add a verified threat record above; sample data is explicitly marked synthetic.</p>';
  for(const button of $('threats').querySelectorAll('[data-edit-threat]'))button.onclick=()=>openThreatEditor(items.find(item=>item.id===button.dataset.editThreat));
  for(const button of $('threats').querySelectorAll('[data-delete-threat]'))button.onclick=()=>deleteThreat(button.dataset.deleteThreat);
}
function renderFeeds(items=[]){
  $('feeditems').innerHTML=items.length?items.map(item=>`<article class="feed-card">
    <div class="card-top"><span class="tag">${esc(item.source)}</span><span class="tag">Unreviewed lead</span>${item.published?`<span class="tag">${esc(item.published)}</span>`:''}</div>
    <h3>${esc(item.title)}</h3><p>${esc(item.summary||'No summary was provided by the feed.')}</p>
    ${safeUrl(item.url)?`<a class="text-link" href="${esc(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">Review original source ↗</a>`:''}
  </article>`).join(''):'<p class="empty-state">No feed leads loaded. Refresh feeds to retrieve current leads.</p>';
}
function renderFindings(items=[]){
  $('findings').innerHTML=items.length?items.map(item=>`<details class="finding-card">
    <summary><div class="card-top"><span class="tag">${esc(item.status||'needs review')}</span><span class="tag">${esc(item.platform||'Unknown platform')}</span><span class="tag">${esc(item.severity||'Severity unknown')}</span></div><h3>${esc(item.title||item.package||'Unlabelled finding')}</h3></summary>
    ${item.package?`<p><strong>Package:</strong> ${esc(item.package)}${item.installed_version?` · installed ${esc(item.installed_version)}`:''}</p>`:''}
    ${item.cve?`<p><strong>Advisory ID:</strong> ${esc(item.cve)}</p>`:''}${item.hostname?`<p><strong>Device:</strong> ${esc(item.hostname)}</p>`:''}
    ${item.recommendation?`<p><strong>Review guidance:</strong> ${esc(item.recommendation)}</p>`:''}
    ${safeUrl(item.source_url)?`<a class="text-link" href="${esc(safeUrl(item.source_url))}" target="_blank" rel="noopener noreferrer">Review advisory ↗</a>`:''}
    <p><strong>Evidence note:</strong> An advisory match does not establish exploitation. Check affected versions with the vendor.</p>
  </details>`).join(''):'<p class="empty-state">No findings match these filters. Run the read-only scanner from the project folder to submit an inventory.</p>';
}
async function refresh(){
  const platform=$('platform').value;
  try{
    const health=await api('/health');
    $('health').textContent=`MongoDB ${health.mongodb==='ok'?'connected':'unavailable'} · Ollama ${health.ollama_models?.length?'ready':'not detected'}`;
    $('health').classList.toggle('secondary',health.mongodb!=='ok'||!health.ollama_models?.length);
  }catch(error){$('health').textContent=`Health check failed: ${error.message}`}
  const threatParams=new URLSearchParams();
  if(platform!=='All')threatParams.set('platform',platform);
  if($('threatStatus').value)threatParams.set('status',$('threatStatus').value);
  if($('threatSearch').value.trim())threatParams.set('search',$('threatSearch').value.trim());
  const findingParams=new URLSearchParams();
  if($('findingPlatform').value)findingParams.set('platform',$('findingPlatform').value);
  if($('findingStatus').value)findingParams.set('status',$('findingStatus').value);
  if($('findingSeverity').value.trim())findingParams.set('severity',$('findingSeverity').value.trim());
  if($('findingSearch').value.trim())findingParams.set('search',$('findingSearch').value.trim());
  const results=await Promise.allSettled([
    api(`/api/threats?${threatParams}`),api('/api/feeds'),api(`/api/findings?${findingParams}`)
  ]);
  if(results[0].status==='fulfilled'){
    const items=results[0].value.items||[];
    statuses.forEach(status=>$(status).textContent=items.filter(item=>item.status===status).length);
    renderThreats(items);
  }else $('threats').innerHTML=`<p class="empty-state">${esc(results[0].reason.message)}</p>`;
  if(results[1].status==='fulfilled')renderFeeds(results[1].value.items||[]);
  else $('feeditems').innerHTML=`<p class="empty-state">${esc(results[1].reason.message)}</p>`;
  if(results[2].status==='fulfilled')renderFindings(results[2].value.items||[]);
  else $('findings').innerHTML=`<p class="empty-state">${esc(results[2].reason.message)}</p>`;
}
function openThreatEditor(item){
  if(!item)return;
  const form=$('editThreatForm');
  for(const name of ['id','title','platform','status','summary','mitigation'])form.elements[name].value=item[name]||'';
  $('editThreatDialog').showModal();
}
async function deleteThreat(id){
  if(!confirm('Delete this threat record? This cannot be undone.'))return;
  try{await api(`/api/threats/${encodeURIComponent(id)}`,{method:'DELETE'});await refresh()}
  catch(error){alert(`Could not delete record: ${error.message}`)}
}
async function loadChat(){
  showAccess();
  $('chatlog').replaceChildren();
  try{
    const result=await api(`/api/chat/${encodeURIComponent(sessionId)}`);
    const messages=result.messages||[];
    for(const message of messages)appendMessage(message.role==='assistant'?'assistant':'user',message.content);
    if(messages.length&&messages[messages.length-1].role==='user')appendMessage('assistant','It looks like I didn’t finish answering your last message. Please send it again and I’ll take another look.',true);
  }catch(error){appendMessage('assistant',`I couldn’t load this conversation: ${error.message}`,true)}
  if(!$('chatlog').children.length)appendMessage('assistant','Hi! I’m SignalWatch. Ask me about the Labs, threat records, scan findings, or defensive steps. I’ll share relevant sources and be clear about uncertainty.');
}

$('chatform').addEventListener('submit',async event=>{
  event.preventDefault();
  const question=$('question').value.trim();
  if(!question)return;
  $('question').value='';appendMessage('user',question);
  const waiting=appendMessage('assistant','Let me check the relevant sources…');
  $('send').disabled=true;showSources();
  try{
    const result=await api('/api/chat',{method:'POST',body:JSON.stringify({message:question,session_id:sessionId,platform:$('platform').value==='All'?null:$('platform').value})});
    waiting.textContent=result.answer;showSources(result.retrieved_sources||[]);
  }catch(error){waiting.classList.add('error');waiting.textContent=`Sorry, I couldn’t complete that request: ${error.message}`}
  finally{$('send').disabled=false;$('question').focus();$('chatlog').scrollTop=$('chatlog').scrollHeight}
});
$('threatForm').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.currentTarget;const data=Object.fromEntries(new FormData(form));for(const key of Object.keys(data))if(!data[key])delete data[key];
  try{await api('/api/threats',{method:'POST',body:JSON.stringify(data)});form.reset();$('threatFormMessage').textContent='Threat record added.';await refresh()}
  catch(error){$('threatFormMessage').textContent=`Could not add threat: ${error.message}`}
});
$('editThreatForm').addEventListener('submit',async event=>{
  event.preventDefault();const data=Object.fromEntries(new FormData(event.currentTarget));const id=data.id;delete data.id;for(const key of Object.keys(data))if(!data[key])delete data[key];
  try{await api(`/api/threats/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify(data)});$('editThreatDialog').close();await refresh()}
  catch(error){alert(`Could not update record: ${error.message}`)}
});
$('cancelThreatEdit').onclick=()=>$('editThreatDialog').close();
$('editThreatDialog').addEventListener('click',event=>{if(event.target===$('editThreatDialog'))$('editThreatDialog').close()});
$('apiKey').onclick=()=>{const value=prompt('Enter the API_TOKEN configured for this SignalWatch server. It is stored only for this browser tab:');if(value!==null){apiKey=value.trim();if(apiKey)sessionStorage.setItem('signalwatch_api_key',apiKey);else sessionStorage.removeItem('signalwatch_api_key');showAccess();refresh()}};
$('clearKey').onclick=()=>{apiKey='';sessionStorage.removeItem('signalwatch_api_key');showAccess();refresh()};
$('refresh').onclick=refresh;
$('platform').onchange=refresh;
$('threatStatus').onchange=refresh;
$('findingPlatform').onchange=refresh;
$('findingStatus').onchange=refresh;
for(const id of ['threatSearch','findingSearch','findingSeverity'])$(id).addEventListener('input',()=>{clearTimeout(window.filterTimer);window.filterTimer=setTimeout(refresh,250)});
$('feeds').onclick=async()=>{const button=$('feeds');button.disabled=true;button.textContent='Refreshing…';try{const result=await api('/api/feeds/refresh',{method:'POST',body:'{}'});alert(`Added ${result.new_reports} new leads.${result.errors.length?`\n${result.errors.join('\n')}`:''}`);await refresh()}catch(error){alert(error.message)}finally{button.disabled=false;button.textContent='Refresh threat feeds'}};
$('scan').onclick=()=>alert('In a terminal opened in the project folder, run: python3 host_agent/scan_host.py (Windows: py host_agent/scan_host.py). The scanner is read-only and submits package inventory and advisory matches for review.');
$('newChat').onclick=()=>{sessionId=crypto.randomUUID();localStorage.setItem('signalwatch_session',sessionId);showSources();loadChat()};
$('clearChat').onclick=async()=>{if(!confirm('Delete the saved messages in this chat?'))return;try{await api(`/api/chat/${encodeURIComponent(sessionId)}`,{method:'DELETE'});showSources();await loadChat()}catch(error){alert(`Could not clear this chat: ${error.message}`)}};
showAccess();refresh();loadChat();
