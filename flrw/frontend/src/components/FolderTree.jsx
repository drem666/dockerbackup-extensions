import React, { useState } from 'react';

const FolderNode = ({ node, selectedPaths, setSelectedPaths }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => setIsOpen(!isOpen);

  // Toggle selection and cascade to children
  const toggleSelection = (path, children) => {
    let newSelection = [...selectedPaths];
    const addPath = (p) => { if (!newSelection.includes(p)) newSelection.push(p); };
    const removePath = (p) => { newSelection = newSelection.filter(item => item !== p); };

    if (newSelection.includes(path)) {
      removePath(path);
      const removeChildren = (nodes) => {
        nodes.forEach(n => {
          newSelection = newSelection.filter(item => item !== n.path);
          if (n.children && n.children.length) removeChildren(n.children);
        });
      };
      if (children) removeChildren(children);
    } else {
      addPath(path);
      const addChildren = (nodes) => {
        nodes.forEach(n => {
          addPath(n.path);
          if (n.children && n.children.length) addChildren(n.children);
        });
      };
      if (children) addChildren(children);
    }
    setSelectedPaths(newSelection);
  };

  // Instead of truncating the beginning, display only the last segment (basename)
  const parts = node.path.split("/");
  const displayName = parts[parts.length - 1] || node.path;

  return (
    <li>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {node.children && node.children.length > 0 && (
          <button onClick={toggleOpen} style={{ marginRight: '5px' }}>
            {isOpen ? '-' : '+'}
          </button>
        )}
        <label>
          <input 
            type="checkbox" 
            checked={selectedPaths.includes(node.path)} 
            onChange={() => toggleSelection(node.path, node.children)} 
          />
          {displayName}
        </label>
      </div>
      {isOpen && node.children && node.children.length > 0 && (
        <ul style={{ marginLeft: '20px' }}>
          {node.children.map(child => (
            <FolderNode key={child.path} node={child} selectedPaths={selectedPaths} setSelectedPaths={setSelectedPaths} />
          ))}
        </ul>
      )}
    </li>
  );
};

const FolderTree = ({ volumes, selectedPaths, setSelectedPaths }) => {
  return (
    <div>
      <ul>
        {volumes.map(volume => (
          <FolderNode key={volume.path} node={volume} selectedPaths={selectedPaths} setSelectedPaths={setSelectedPaths} />
        ))}
      </ul>
    </div>
  );
};

export default FolderTree;
