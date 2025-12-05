/**
 * Agent Management - List and discover agents
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, RefreshCw, Database, CheckCircle, XCircle } from 'lucide-react';
import { Card, Spinner, EmptyState, Badge, Modal } from '../../components/ui';
import api from '../../api/services';
import { toast } from 'sonner';

const AgentList: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [discoverModal, setDiscoverModal] = useState(false);
  const [discoveryEndpoint, setDiscoveryEndpoint] = useState('');

  const { data: agentsResponse, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.agents.list().then((res) => res.data),
  });

  // Extract agents array from response
  const agents = agentsResponse?.agents || [];

  const discoverMutation = useMutation({
    mutationFn: () => api.agents.discover(discoveryEndpoint),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast.success(`Discovered ${response.data.agents.length} agents`);
      setDiscoverModal(false);
      setDiscoveryEndpoint('');
    },
    onError: () => {
      toast.error('Failed to discover agents');
    },
  });

  const filteredAgents = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.keywords.some(k => k.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (isLoading) return <Spinner />;

  return (
    <div className="agent-list">
      <div className="page-header">
        <div>
          <h1>Agent Management</h1>
          <p className="text-secondary">Manage and discover DataAgents</p>
        </div>
        <button onClick={() => setDiscoverModal(true)} className="button button-primary">
          <RefreshCw size={16} />
          Discover Agents
        </button>
      </div>

      <Card className="mb-6">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </Card>

      {filteredAgents.length === 0 ? (
        <EmptyState
          icon={<Database size={48} />}
          title="No agents found"
          description={
            searchTerm
              ? 'Try adjusting your search criteria'
              : 'Discover agents from your FoundryIQ endpoints'
          }
          action={
            !searchTerm && (
              <button onClick={() => setDiscoverModal(true)} className="button button-primary">
                <RefreshCw size={16} />
                Discover Agents
              </button>
            )
          }
        />
      ) : (
        <div className="agent-grid">
          {filteredAgents.map((agent) => (
            <Card key={agent.id} className="agent-card">
              <div className="agent-card-header">
                <div className="agent-icon">
                  <Database size={24} />
                </div>
                <div className="agent-info">
                  <h3 className="agent-name">{agent.name}</h3>
                  <p className="agent-type">{agent.foundry_agent_id}</p>
                </div>
                <Badge variant={agent.status === 'active' ? 'success' : 'error'}>
                  {agent.status === 'active' ? (
                    <>
                      <CheckCircle size={14} /> Active
                    </>
                  ) : (
                    <>
                      <XCircle size={14} /> Inactive
                    </>
                  )}
                </Badge>
              </div>

              <p className="agent-description">{agent.description}</p>

              <div className="agent-capabilities">
                <strong>Knowledge Sources:</strong>
                <div className="capability-tags">
                  {agent.knowledge_sources.map((source, idx) => (
                    <span key={idx} className="capability-tag">
                      {source}
                    </span>
                  ))}
                </div>
              </div>

              {agent.keywords.length > 0 && (
                <div className="agent-metadata">
                  <strong>Keywords:</strong>
                  <div className="capability-tags">
                    {agent.keywords.map((keyword, idx) => (
                      <span key={idx} className="capability-tag">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Discovery Modal */}
      <Modal
        isOpen={discoverModal}
        onClose={() => setDiscoverModal(false)}
        title="Discover Agents"
        footer={
          <>
            <button onClick={() => setDiscoverModal(false)} className="button button-secondary">
              Cancel
            </button>
            <button
              onClick={() => discoverMutation.mutate()}
              className="button button-primary"
              disabled={!discoveryEndpoint || discoverMutation.isPending}
            >
              {discoverMutation.isPending ? 'Discovering...' : 'Discover'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label htmlFor="endpoint" className="form-label">
            FoundryIQ Endpoint
          </label>
          <input
            id="endpoint"
            type="url"
            className="input"
            value={discoveryEndpoint}
            onChange={(e) => setDiscoveryEndpoint(e.target.value)}
            placeholder="https://foundry.azure.com/..."
          />
          <p className="form-hint">
            Enter the FoundryIQ endpoint URL to discover available agents
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default AgentList;
