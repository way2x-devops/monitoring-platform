import React, { useState, useEffect } from 'react'

function App() {
  const [containers, setContainers] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/containers')
        const data = await response.json()
        setContainers(data)
      } catch (error) {
        console.error('Failed to fetch:', error)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <h1>🚀 Docker Containers Monitor</h1>
      {containers.map(container => (
        <div key={container.name} style={{ 
          margin: '10px', 
          padding: '10px', 
          border: '1px solid #ccc',
          backgroundColor: container.status === 'running' ? '#e8f5e8' : '#f5e8e8'
        }}>
          <strong>{container.name}</strong> - {container.status}
        </div>
      ))}
    </div>
  )
}

export default App