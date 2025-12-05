/**
 * Notifications Center
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Check, CheckCheck, Settings as SettingsIcon } from 'lucide-react';
import { Card, Spinner, EmptyState, Badge, Modal } from '../../components/ui';
import api from '../../api/services';
import type { Notification } from '../../types';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

const NotificationCenter: React.FC = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [preferencesModal, setPreferencesModal] = useState(false);
  const [selectedChannels, setSelectedChannels] = useState<string[]>(['in-app']);

  const { data: notifications, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.notifications.list().then((res) => res.data),
  });

  const { data: _preferences } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => api.notifications.getPreferences().then((res) => res.data),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.notifications.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => api.notifications.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success('All notifications marked as read');
    },
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: (channels: string[]) => api.notifications.setPreferences(channels),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
      setPreferencesModal(false);
      toast.success('Preferences updated');
    },
  });

  const filteredNotifications = notifications?.filter((n) =>
    filter === 'unread' ? !n.read : true
  );

  const unreadCount = notifications?.filter((n) => !n.read).length || 0;

  if (isLoading) return <Spinner />;

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className="notification-center">
      <div className="page-header">
        <div>
          <h1>Notifications</h1>
          <p className="text-secondary">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}` : 'All caught up!'}
          </p>
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button
              onClick={() => markAllReadMutation.mutate()}
              className="button button-secondary"
              disabled={markAllReadMutation.isPending}
            >
              <CheckCheck size={16} />
              Mark All Read
            </button>
          )}
          <button onClick={() => setPreferencesModal(true)} className="button button-secondary">
            <SettingsIcon size={16} />
            Preferences
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <Card className="mb-6">
        <div className="tabs">
          <button
            onClick={() => setFilter('all')}
            className={`tab ${filter === 'all' ? 'active' : ''}`}
          >
            All Notifications
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`tab ${filter === 'unread' ? 'active' : ''}`}
          >
            Unread {unreadCount > 0 && `(${unreadCount})`}
          </button>
        </div>
      </Card>

      {/* Notifications List */}
      {filteredNotifications?.length === 0 ? (
        <EmptyState
          icon={<Bell size={48} />}
          title={filter === 'unread' ? 'No unread notifications' : 'No notifications'}
          description={
            filter === 'unread'
              ? 'All notifications have been read'
              : "You haven't received any notifications yet"
          }
        />
      ) : (
        <div className="notification-list">
          {filteredNotifications?.map((notification) => (
            <Card
              key={notification.id}
              className={`notification-item ${!notification.read ? 'unread' : ''}`}
            >
              <div className="notification-header">
                <div className="notification-icon">{getNotificationIcon(notification.type)}</div>
                <div className="notification-content">
                  <div className="notification-title-row">
                    <h4 className="notification-title">{notification.title}</h4>
                    <Badge variant={notification.type}>{notification.type}</Badge>
                  </div>
                  <p className="notification-message">{notification.message}</p>
                  <div className="notification-meta">
                    <span className="notification-time">
                      {formatDistanceToNow(new Date(notification.timestamp), {
                        addSuffix: true,
                      })}
                    </span>
                    {!notification.read && <Badge variant="info">New</Badge>}
                  </div>
                </div>
                <div className="notification-actions">
                  {!notification.read && (
                    <button
                      onClick={() => markReadMutation.mutate(notification.id)}
                      className="button button-sm button-ghost"
                      title="Mark as read"
                    >
                      <Check size={16} />
                    </button>
                  )}
                  {notification.action_url && (
                    <a
                      href={notification.action_url}
                      className="button button-sm button-primary"
                    >
                      View
                    </a>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Preferences Modal */}
      <Modal
        isOpen={preferencesModal}
        onClose={() => setPreferencesModal(false)}
        title="Notification Preferences"
        footer={
          <>
            <button onClick={() => setPreferencesModal(false)} className="button button-secondary">
              Cancel
            </button>
            <button
              onClick={() => updatePreferencesMutation.mutate(selectedChannels)}
              className="button button-primary"
              disabled={updatePreferencesMutation.isPending}
            >
              Save Preferences
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Notification Channels</label>
          <div className="checkbox-group">
            <label className="form-checkbox">
              <input
                type="checkbox"
                checked={selectedChannels.includes('in-app')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedChannels([...selectedChannels, 'in-app']);
                  } else {
                    setSelectedChannels(selectedChannels.filter((c) => c !== 'in-app'));
                  }
                }}
              />
              <span>In-App Notifications</span>
            </label>
            <label className="form-checkbox">
              <input
                type="checkbox"
                checked={selectedChannels.includes('email')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedChannels([...selectedChannels, 'email']);
                  } else {
                    setSelectedChannels(selectedChannels.filter((c) => c !== 'email'));
                  }
                }}
              />
              <span>Email Notifications</span>
            </label>
            <label className="form-checkbox">
              <input
                type="checkbox"
                checked={selectedChannels.includes('sms')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedChannels([...selectedChannels, 'sms']);
                  } else {
                    setSelectedChannels(selectedChannels.filter((c) => c !== 'sms'));
                  }
                }}
              />
              <span>SMS Notifications</span>
            </label>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default NotificationCenter;
