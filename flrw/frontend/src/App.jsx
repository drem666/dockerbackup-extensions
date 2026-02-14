import React, { useEffect, useState } from 'react';
import FolderTree from './components/FolderTree';
import axios from 'axios';

const App = () => {
  const [volumes, setVolumes] = useState([]);
  const [selectedPaths, setSelectedPaths] = useState([]);
  const [destination, setDestination] = useState(""); // Manual Docker path
  const [windowsPath, setWindowsPath] = useState(""); // Windows folder path input

  useEffect(() => {
    axios.get('/api/volumes')
      .then(response => setVolumes(response.data))
      .catch(error => console.error("Error fetching volumes:", error));
  }, []);

  // Converts a Windows folder path (e.g. "D:\Folder1\Folder 2\Folder 3")
  // to a Docker path: "/tmp/docker-desktop-root/run/desktop/mnt/host/d/Folder1/Folder 2/Folder 3"
  const convertWindowsPathToDocker = (winPath) => {
    if (!winPath) return "";
    const match = winPath.match(/^([A-Za-z]):\\(.*)/);
    if (!match) return "";
    const drive = match[1].toLowerCase();
    const rest = match[2].replace(/\\/g, "/");
    return `/tmp/docker-desktop-root/run/desktop/mnt/host/${drive}/${rest}`;
  };

  const handleBackup = () => {
    // Use converted Windows path if provided; otherwise, manual destination
    const finalDestination = windowsPath ? convertWindowsPathToDocker(windowsPath) : destination;
    if (!finalDestination) {
      alert("Please provide a backup destination.");
      return;
    }
    axios.post('/api/backup', { paths: selectedPaths, destination: finalDestination })
      .then(response => alert(response.data.status))
      .catch(error => {
        const errMsg = error.response?.data?.error || error.message;
        alert("Backup failed: " + errMsg);
      });
  };

  return (
    <div>
      <h1>Docker Backup Extension</h1>
      <FolderTree volumes={volumes} selectedPaths={selectedPaths} setSelectedPaths={setSelectedPaths} />
      <div>
        <label>
          Backup Destination (Docker Path):
          <input 
            type="text" 
            value={destination} 
            onChange={e => setDestination(e.target.value)} 
            placeholder="/tmp/docker-desktop-root/run/desktop/mnt/host/..."
          />
        </label>
      </div>
      <div>
        <label>
          OR Enter Windows Folder Path:
          <input 
            type="text" 
            value={windowsPath} 
            onChange={e => setWindowsPath(e.target.value)} 
            placeholder="D:\Folder1\Folder 2\Folder 3"
          />
        </label>
        <p>
          Will be converted to Docker path: {windowsPath && convertWindowsPathToDocker(windowsPath)}
        </p>
      </div>
      <button onClick={handleBackup}>Run Backup</button>
    </div>
  );
};

export default App;
