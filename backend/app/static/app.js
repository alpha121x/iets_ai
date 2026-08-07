const api = "/api";
let mode = "login";
const token = () => localStorage.getItem("ai_coach_token");
const request = async (path, options = {}) => {
  const headers = options.body instanceof FormData ? {} : {"Content-Type": "application/json"};
  if (token()) headers.Authorization = `Bearer ${token()}`;
  const response = await fetch(api + path, {...options, headers: {...headers, ...options.headers}});
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "Request failed");
  return response.json();
};

document.querySelectorAll("[data-tab]").forEach(button => button.onclick = () => {
  mode = button.dataset.tab;
  document.querySelectorAll("[data-tab]").forEach(item => item.classList.toggle("active", item === button));
  document.querySelector("#name").hidden = mode !== "register";
  document.querySelector("#password").autocomplete = mode === "login" ? "current-password" : "new-password";
});
document.querySelector("#auth-form").onsubmit = async event => {
  event.preventDefault(); const error = document.querySelector("#auth-error"); error.textContent = "";
  const email = document.querySelector("#email").value, password = document.querySelector("#password").value;
  try {
    let data;
    if (mode === "register") data = await request("/auth/register", {method:"POST", body:JSON.stringify({email,password,full_name:document.querySelector("#name").value})});
    else { const body = new URLSearchParams({username:email,password}); data = await request("/auth/login", {method:"POST", body, headers:{"Content-Type":"application/x-www-form-urlencoded"}}); }
    localStorage.setItem("ai_coach_token", data.access_token); showDashboard();
  } catch (e) { error.textContent = e.message; }
};
document.querySelector("#logout").onclick = () => { localStorage.removeItem("ai_coach_token"); location.reload(); };
document.querySelector("#refresh").onclick = () => loadDashboard();
document.querySelector("#score-form").onsubmit = async event => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.target));
  Object.keys(data).forEach(key => data[key] = Number(data[key]));
  try { await request("/ielts/results", {method:"POST", body:JSON.stringify(data)}); event.target.reset(); loadDashboard(); } catch(e) { alert(e.message); }
};
document.querySelector("#profile-form").onsubmit = async event => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.target));
  if (data.cgpa) data.cgpa = Number(data.cgpa); else delete data.cgpa;
  try { await request("/profile/me", {method:"PUT", body:JSON.stringify(data)}); loadDashboard(); } catch(e) { alert(e.message); }
};
async function showDashboard() {
  document.querySelector("#auth-card").hidden = true; document.querySelector("#dashboard").hidden = false; document.querySelector("#logout").hidden = false;
  await loadDashboard();
}
async function loadDashboard() {
  try {
    const [dashboard, profile, lessons, recs] = await Promise.all([request("/dashboard"), request("/profile/me"), request("/ielts/lessons"), request("/universities/recommendations")]);
    document.querySelector("#welcome").textContent = `Welcome, ${dashboard.student}`;
    document.querySelector("#overall").textContent = dashboard.ielts?.overall ?? "—";
    document.querySelector("#focus").textContent = dashboard.weakest_module ?? "—";
    document.querySelector("#matches").textContent = dashboard.strong_matches;
    document.querySelector("#summary").textContent = dashboard.ielts ? `Your current focus is ${dashboard.weakest_module}.` : "Record an IELTS score to unlock eligibility matching.";
    document.querySelector("#profile-form").target_country.value = profile.target_country || "";
    document.querySelector("#profile-form").target_program.value = profile.target_program || "";
    document.querySelector("#profile-form").cgpa.value = profile.cgpa || "";
    document.querySelector("#lessons").innerHTML = lessons.map(l => `<div class="lesson"><strong>${l.module} · ${l.level}</strong><b>${l.title}</b><p>${l.content}</p></div>`).join("");
    document.querySelector("#recommendations").innerHTML = recs.length ? recs.map(r => `<div class="recommendation"><div><b>${r.university}</b><br><span>${r.program} · ${r.country}</span><p>${r.reasons?.join("; ") || `IELTS minimum ${r.min_ielts ?? "varies"} · CGPA minimum ${r.min_cgpa ?? "varies"}`}</p></div><span class="badge ${r.status === "Strong match" ? "strong" : r.status === "Possible match" ? "possible" : r.status === "Profile incomplete" ? "incomplete" : "not"}">${r.status} · ${r.match_percentage}%</span></div>`).join("") : "<p>No sample programmes match your selected country/field yet. Edit your profile or add verified programme data.</p>";
  } catch (e) { if (e.message.includes("validate credentials")) { localStorage.removeItem("ai_coach_token"); location.reload(); } else alert(e.message); }
}
if (token()) showDashboard();
