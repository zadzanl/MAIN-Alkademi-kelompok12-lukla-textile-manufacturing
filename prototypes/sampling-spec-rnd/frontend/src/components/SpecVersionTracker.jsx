/**
 * @name: SpecVersionTracker
 * @description: Component untuk track versi spesifikasi produk dan prevent R&D drift
 * @params: {string} productId - ID produk
 * @params: {array} versions - Array of spec versions
 * @params: {function} onVersionCreated - Callback saat versi baru dibuat
 * @returns: JSX component
 * @example:
 *   <SpecVersionTracker productId="prod-123" versions={specs} onVersionCreated={handleNew} />
 */

import React, { useState } from 'react';

const SpecVersionTracker = ({ productId, versions = [], onVersionCreated }) => {
  const [showNewVersionForm, setShowNewVersionForm] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [newVersionData, setNewVersionData] = useState({
    description: '',
    changes: '',
    status: 'draft',
  });

  // Handle create new version
  const handleCreateVersion = async () => {
    if (!newVersionData.description.trim()) {
      alert('Deskripsi versi harus diisi');
      return;
    }

    try {
      const newVersion = {
        id: `spec-${Date.now()}`,
        productId,
        versionNumber: versions.length + 1,
        description: newVersionData.description,
        changes: newVersionData.changes,
        status: newVersionData.status,
        createdAt: new Date().toISOString(),
        createdBy: 'current-user', // Replace dengan actual user
        changeLog: {
          type: 'initial',
          timestamp: new Date().toISOString(),
        },
      };

      onVersionCreated?.(newVersion);

      // Reset form
      setNewVersionData({ description: '', changes: '', status: 'draft' });
      setShowNewVersionForm(false);
      alert('Versi spesifikasi berhasil dibuat!');
    } catch (error) {
      console.error('Error creating version:', error);
      alert('Gagal membuat versi spesifikasi');
    }
  };

  // Get version badge color
  const getStatusColor = (status) => {
    const colors = {
      draft: '#FFA500',
      approved: '#4CAF50',
      deprecated: '#F44336',
      archived: '#9E9E9E',
    };
    return colors[status] || '#666';
  };

  return (
    <div className="spec-version-tracker">
      <div className="tracker-header">
        <h2>Spec Version Tracker</h2>
        <p className="product-id">Product ID: {productId}</p>
      </div>

      {/* New Version Button */}
      <button 
        className="btn-primary"
        onClick={() => setShowNewVersionForm(!showNewVersionForm)}
      >
        {showNewVersionForm ? 'Cancel' : '+ New Version'}
      </button>

      {/* New Version Form */}
      {showNewVersionForm && (
        <div className="new-version-form">
          <div className="form-group">
            <label>Deskripsi Versi</label>
            <textarea
              value={newVersionData.description}
              onChange={(e) => setNewVersionData({
                ...newVersionData,
                description: e.target.value,
              })}
              placeholder="e.g., Versi 1.0 dengan padding 5mm dan jahitan 2mm"
              rows="3"
              className="textarea-field"
            />
          </div>

          <div className="form-group">
            <label>Perubahan / Catatan</label>
            <textarea
              value={newVersionData.changes}
              onChange={(e) => setNewVersionData({
                ...newVersionData,
                changes: e.target.value,
              })}
              placeholder="Detail perubahan dari versi sebelumnya"
              rows="2"
              className="textarea-field"
            />
          </div>

          <div className="form-group">
            <label>Status</label>
            <select
              value={newVersionData.status}
              onChange={(e) => setNewVersionData({
                ...newVersionData,
                status: e.target.value,
              })}
              className="select-field"
            >
              <option value="draft">Draft</option>
              <option value="approved">Approved</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>

          <button 
            className="btn-save"
            onClick={handleCreateVersion}
          >
            Create Version
          </button>
        </div>
      )}

      {/* Versions List */}
      <div className="versions-list">
        <h3>Available Versions ({versions.length})</h3>
        {versions.length === 0 ? (
          <p className="empty-state">Belum ada versi spesifikasi</p>
        ) : (
          <div className="versions-grid">
            {versions.map((version) => (
              <div 
                key={version.id}
                className={`version-card ${selectedVersion?.id === version.id ? 'selected' : ''}`}
                onClick={() => setSelectedVersion(version)}
              >
                <div className="version-header">
                  <h4>Version {version.versionNumber}</h4>
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(version.status) }}
                  >
                    {version.status}
                  </span>
                </div>
                <p className="description">{version.description}</p>
                <div className="metadata">
                  <small>Created: {new Date(version.createdAt).toLocaleDateString('id-ID')}</small>
                  <small>By: {version.createdBy}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Version Detail */}
      {selectedVersion && (
        <div className="version-detail">
          <div className="detail-header">
            <h3>Version {selectedVersion.versionNumber} Details</h3>
            <button 
              className="btn-close"
              onClick={() => setSelectedVersion(null)}
            >
              ×
            </button>
          </div>
          
          <div className="detail-content">
            <div className="detail-row">
              <strong>Description:</strong>
              <p>{selectedVersion.description}</p>
            </div>

            <div className="detail-row">
              <strong>Changes:</strong>
              <p>{selectedVersion.changes || 'No changes recorded'}</p>
            </div>

            <div className="detail-row">
              <strong>Status:</strong>
              <span style={{ backgroundColor: getStatusColor(selectedVersion.status) }}>
                {selectedVersion.status}
              </span>
            </div>

            <div className="detail-row">
              <strong>Created:</strong>
              <p>{new Date(selectedVersion.createdAt).toLocaleString('id-ID')}</p>
            </div>

            {selectedVersion.changeLog && (
              <div className="detail-row">
                <strong>Change Log:</strong>
                <pre>{JSON.stringify(selectedVersion.changeLog, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SpecVersionTracker;
