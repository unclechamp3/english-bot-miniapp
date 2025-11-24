import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import './Charts.css'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

function Charts({ dailyData, errorTypes }) {
  // Prepare daily activity chart data
  const dailyChartData = {
    labels: dailyData.map(d => {
      const date = new Date(d.date)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }),
    datasets: [
      {
        label: 'Messages',
        data: dailyData.map(d => d.messages),
        borderColor: 'rgb(0, 122, 255)',
        backgroundColor: 'rgba(0, 122, 255, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const dailyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  }

  // Prepare error types chart data
  const errorTypeLabels = Object.keys(errorTypes)
  const errorTypeValues = Object.values(errorTypes)

  const errorChartData = {
    labels: errorTypeLabels.map(label => {
      // Convert snake_case to Title Case
      return label.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }),
    datasets: [
      {
        label: 'Errors',
        data: errorTypeValues,
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
        ],
      },
    ],
  }

  const errorChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  }

  return (
    <div className="charts">
      <div className="chart-container">
        <h3 className="chart-title">📊 Activity (Last 7 Days)</h3>
        <div className="chart-wrapper">
          <Line data={dailyChartData} options={dailyChartOptions} />
        </div>
      </div>

      {errorTypeLabels.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title">🎯 Error Types</h3>
          <div className="chart-wrapper">
            <Bar data={errorChartData} options={errorChartOptions} />
          </div>
        </div>
      )}
    </div>
  )
}

export default Charts

