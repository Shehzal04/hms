// HostelFlow Main SaaS Scripts
document.addEventListener('DOMContentLoaded', function () {
  // 1. Sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarWrapper = document.getElementById('sidebar-wrapper');
  if (sidebarToggle && sidebarWrapper) {
    sidebarToggle.addEventListener('click', function (e) {
      e.preventDefault();
      sidebarWrapper.classList.toggle('d-none');
    });
  }

  // 2. Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (el) {
    return new bootstrap.Tooltip(el);
  });

  // 3. Mark Notification as Read
  document.querySelectorAll('.mark-notif-read-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const notifId = this.dataset.id;
      const notifItem = document.getElementById(`notif-item-${notifId}`);
      fetch(`/portal/notifications/mark-read/${notifId}`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : ''
        }
      }).then(() => {
        if (notifItem) notifItem.classList.add('opacity-50');
        const badge = document.getElementById('unread-notif-badge');
        if (badge) {
          let count = parseInt(badge.textContent) - 1;
          if (count > 0) badge.textContent = count;
          else badge.style.display = 'none';
        }
      });
    });
  });

  // 4. Dynamic Dependent Bed Dropdown for Room Allocation Form
  const roomSelect = document.getElementById('room_id') || document.getElementById('new_room_id');
  const bedSelect = document.getElementById('bed_id') || document.getElementById('new_bed_id');
  if (roomSelect && bedSelect) {
    roomSelect.addEventListener('change', function () {
      const roomId = this.value;
      bedSelect.innerHTML = '<option value="">Loading beds...</option>';
      if (!roomId) {
        bedSelect.innerHTML = '<option value="">-- Select Room First --</option>';
        return;
      }
      fetch(`/allocations/api/beds-by-room/${roomId}`)
        .then(res => res.json())
        .then(beds => {
          bedSelect.innerHTML = '';
          if (beds.length === 0) {
            bedSelect.innerHTML = '<option value="">No available beds in this room</option>';
          } else {
            beds.forEach(b => {
              const opt = document.createElement('option');
              opt.value = b.id;
              opt.textContent = `${b.bed_number} (Available)`;
              bedSelect.appendChild(opt);
            });
          }
        })
        .catch(err => {
          bedSelect.innerHTML = '<option value="">Failed to load beds</option>';
        });
    });
  }

  // 5. Dashboard Charts initialization
  const revenueChartCanvas = document.getElementById('revenueChart');
  const admissionsChartCanvas = document.getElementById('admissionsChart');
  const occupancyChartCanvas = document.getElementById('occupancyChart');
  const attendanceChartCanvas = document.getElementById('attendanceChart');

  if (revenueChartCanvas) {
    fetch('/api/dashboard/chart-data')
      .then(res => res.json())
      .then(data => {
        // Chart 1: Revenue Line Chart
        new Chart(revenueChartCanvas, {
          type: 'line',
          data: {
            labels: data.revenue.labels,
            datasets: [{
              label: 'Monthly Fee Collection (PKR)',
              data: data.revenue.data,
              borderColor: '#0d6efd',
              backgroundColor: 'rgba(13, 110, 253, 0.1)',
              tension: 0.35,
              fill: true,
              pointBackgroundColor: '#0d6efd',
              pointRadius: 5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function (value) {
                    return 'Rs. ' + value.toLocaleString();
                  }
                }
              }
            }
          }
        });

        // Chart 2: Admissions by Department Bar Chart
        if (admissionsChartCanvas && data.admissions_by_dept.labels.length > 0) {
          new Chart(admissionsChartCanvas, {
            type: 'bar',
            data: {
              labels: data.admissions_by_dept.labels,
              datasets: [{
                label: 'Enrolled Students',
                data: data.admissions_by_dept.data,
                backgroundColor: '#3b82f6',
                borderRadius: 6
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
            }
          });
        }

        // Chart 3: Room Occupancy Doughnut Chart
        if (occupancyChartCanvas) {
          new Chart(occupancyChartCanvas, {
            type: 'doughnut',
            data: {
              labels: data.occupancy.labels,
              datasets: [{
                data: data.occupancy.data,
                backgroundColor: ['#dc2626', '#10b981', '#f59e0b'],
                hoverOffset: 4
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12 } }
              },
              cutout: '70%'
            }
          });
        }

        // Chart 4: Attendance Overview Polar Area
        if (attendanceChartCanvas) {
          new Chart(attendanceChartCanvas, {
            type: 'pie',
            data: {
              labels: data.attendance_stats.labels,
              datasets: [{
                data: data.attendance_stats.data,
                backgroundColor: ['#10b981', '#ef4444', '#f59e0b']
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12 } }
              }
            }
          });
        }
      })
      .catch(err => console.error('Error fetching dashboard chart data:', err));
  }
});
