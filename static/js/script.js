// Fade-in page load
document.addEventListener("DOMContentLoaded", () => {
  document.body.style.opacity = 0;
  setTimeout(() => {
    document.body.style.transition = "opacity 0.8s ease-in-out";
    document.body.style.opacity = 1;
  }, 100);
});

// Ripple effect
document.querySelectorAll("button, a").forEach(el => {
  el.addEventListener("click", function(e){
    let ripple = document.createElement("span");
    ripple.classList.add("ripple");
    this.appendChild(ripple);
    ripple.style.left = `${e.clientX - this.getBoundingClientRect().left}px`;
    ripple.style.top = `${e.clientY - this.getBoundingClientRect().top}px`;
    setTimeout(() => ripple.remove(), 600);
  });
});

// -------- Watch-face draggable picker ----------
const hourHand = document.querySelector('.hand.hour');
const minuteHand = document.querySelector('.hand.minute');
const centerDot = document.querySelector('.center-dot');
const displayHours = document.getElementById('display-hours');
const displayMinutes = document.getElementById('display-minutes');
const hiddenInput = document.getElementById('arrival_time_hidden');
const destinationForm = document.getElementById('destination-form');
const watchFace = document.querySelector('.watch-face');

if (hourHand && minuteHand && displayHours && displayMinutes && hiddenInput && destinationForm && watchFace) {
  // compute radius
  const rect = watchFace.getBoundingClientRect();
  const watchRadius = rect.width / 2 - 8; // border correction only

  // clear old markers if any
  watchFace.querySelectorAll('.marker').forEach(m => m.remove());

  // Add minute markers
  for (let i = 0; i < 60; i++) {
    const marker = document.createElement('div');
    marker.classList.add('marker');
    if (i % 5 === 0) marker.classList.add('quarter');
    marker.style.left = '50%';
    marker.style.top = '50%';
    marker.style.transform = `translate(-50%,-50%) rotate(${i * 6}deg) translateY(-${watchRadius}px)`;
    watchFace.appendChild(marker);
  }

  let hour = 9, minute = 0, dragging = null;

  function updateHands(){
    hourHand.style.transform = `rotate(${(hour % 12) * 30 + minute * 0.5}deg)`;
    minuteHand.style.transform = `rotate(${minute * 6}deg)`;
    displayHours.textContent = String(hour).padStart(2,'0');
    displayMinutes.textContent = String(minute).padStart(2,'0');
    hiddenInput.value = `${displayHours.textContent}:${displayMinutes.textContent}`;
  }

  function angleFromCenter(e){
    const rect = watchFace.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width/2;
    const y = e.clientY - rect.top - rect.height/2;
    let angle = Math.atan2(y, x) * 180/Math.PI + 90;
    if(angle < 0) angle += 360;
    return angle;
  }

  function updateDrag(e){
    if(!dragging) return;
    const angle = angleFromCenter(e);
    if (dragging === 'hour') {
      hour = Math.round(angle / 30);
      if (hour === 0) hour = 12;
    } else {
      minute = Math.round(angle / 6) % 60;
    }
    updateHands();
  }

  watchFace.addEventListener('mousedown', e => {
    const rect = watchFace.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width/2;
    const y = e.clientY - rect.top - rect.height/2;
    const distance = Math.sqrt(x*x + y*y);
    dragging = (distance < rect.width/4) ? 'hour' : 'minute';
    updateDrag(e);
  });

  document.addEventListener('mousemove', updateDrag);
  document.addEventListener('mouseup', () => dragging = null);

  updateHands();

  destinationForm.addEventListener('submit', e => {
    // hiddenInput already updated by dragging
  });
}

// -------- Students loading popup ----------
const studentsForm = document.getElementById('students-form');
const loadingPopup = document.getElementById('loading-popup');

if (studentsForm && loadingPopup) {
  studentsForm.addEventListener('submit', function(e){
    e.preventDefault();
    const checked = [...studentsForm.elements['students']].some(el=>el.checked);
    if(!checked){ alert('Please select at least one student.'); return; }
    loadingPopup.style.display = 'flex';
    setTimeout(()=>studentsForm.submit(), 2000);
  });
}
