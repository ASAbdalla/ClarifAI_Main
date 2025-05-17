import React, { useState, ChangeEvent } from 'react';
import './ClassClarityMonitor.css';

type TranscriptionLine = {
  text: string;
  attention: number;
  timestamp: string;
};

type Alert = {
  id: number;
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
};

const ClassClarityMonitor: React.FC = () => {
  const [isFeedActive, setIsFeedActive] = useState<boolean>(true);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [attentionRate, setAttentionRate] = useState<number>(50);
  const [comprehensionRate, setComprehensionRate] = useState<number>(40);
  const [activeStudents, setActiveStudents] = useState<number>(6);

  // Physics lesson transcription for kids
  const transcription: TranscriptionLine[] = [
    { text: "Today we're learning about forces and motion!", attention: 92, timestamp: '00:01:15' },
    { text: "A force is a push or pull that makes things move.", attention: 90, timestamp: '00:02:30' },
    { text: "Let's try an experiment with this toy car and ramp!", attention: 95, timestamp: '00:04:10' },
    { text: "What happens when we make the ramp steeper? The car goes faster!", attention: 89, timestamp: '00:06:45' },
    { text: "This is because gravity pulls harder on steeper slopes.", attention: 85, timestamp: '00:08:20' },
    { text: "Now let's see what friction does...", attention: 87, timestamp: '00:10:05' },
    { text: "When we add rough sandpaper, the car slows down!", attention: 80, timestamp: '00:12:30' },
    { text: "Friction is a force that works against motion.", attention: 75, timestamp: '00:14:15' },
    { text: "Can anyone think of examples of friction in everyday life?", attention: 60, timestamp: '00:16:40' },
    { text: "Great answers! Brakes on bikes use friction to stop.", attention: 50, timestamp: '00:19:10' },
  ];

  const alerts: Alert[] = [
    
    { id: 2, message: "Comprehension is high during experiments", severity: 'low',timestamp: '00:05:22' },
    { id: 1, message: "2 students are distracted ", severity: 'medium', timestamp: '00:11:35'  },
    { id: 3, message: "6 students are distracted ", severity: 'high', timestamp: '00:19:10'  },
  ];

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setSelectedImage(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const getAttentionClass = (attention: number): string => {
    if (attention >= 85) return 'high-attention';
    if (attention >= 70) return 'medium-attention';
    return 'low-attention';
  };

  return (
    <div className="class-clarity-monitor">
      
      <div className="dashboard-container">
        {/* Left Column (70% width) */}
        <div className="left-column">
          {/* Video Feed Section - Takes 70% of height */}
          <div className="video-container">
            <div className="dashboard-section feed-section">
              <h2>Live Classroom Feed</h2>
              <div className="video-wrapper">
                {selectedImage ? (
                  <img src={selectedImage} alt="Classroom feed" className="classroom-image" />
                ) : (
                  <div className="video-placeholder">
                    <p>Physics class in progress</p>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleImageUpload}
                      className="image-upload"
                      id="image-upload"
                    />
                    <label htmlFor="image-upload" className="upload-label">
                      Upload Classroom Image
                    </label>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Transcription Section - Takes 30% of height */}
          <div className="transcription-container">
            <div className="dashboard-section transcription-section">
              <h1>Lesson Transcript</h1>
              <div className="transcription-content">
                <div className="transcription-list">
                  {transcription.map((line, index) => (
                    <div 
                      key={index} 
                      className={`transcription-line ${getAttentionClass(line.attention)}`}
                    >
                      <span className="timestamp">[{line.timestamp}]</span>
                      <span className="text">{line.text}</span>
                      <span className="attention-badge">{line.attention}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (30% width) */}
        <div className="right-column">
          {/* Alerts Section */}
          <div className="dashboard-section alerts-section">
            <h1>Alerts</h1>
            <div className="alerts-list">
              {alerts.map(alert => (
                <div key={alert.id} className={`alert-item ${alert.severity}`}>
                  <span className="alert-timestamp">[{alert.timestamp}]</span>
                  <span className="alert-message">{alert.message}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Classroom Metrics Section */}
          <div className="dashboard-section metrics-section">
            <h1>Classroom Metrics</h1>
            <div className="metric">
              <h2>Attention Rate ({attentionRate}%)</h2>
              <div className="metric-bar-container">
                <div 
                  className="metric-bar"
                  style={{ width: `${attentionRate}%` }}
                  data-value={attentionRate}
                ></div>
              </div>
            </div>
            
            <div className="metric">
              <h2>Comprehension Rate ({comprehensionRate}%)</h2>
              <div className="metric-bar-container">
                <div 
                  className="metric-bar"
                  style={{ width: `${comprehensionRate}%` }}
                  data-value={comprehensionRate}
                ></div>
              </div>
            </div>
            
            <div className="active-students">
              <strong>Active Students</strong> {activeStudents} / 12
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClassClarityMonitor;