import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { getApiBaseUrl } from '../api/client';

interface HeaderProps {
  activeTab: 'studio' | 'trace' | 'outfit' | 'blend';
  setActiveTab: (tab: 'studio' | 'trace' | 'outfit' | 'blend') => void;
  isBackendHealthy: boolean;
  itemCount: number;
  engine?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isBackendHealthy,
  itemCount,
  engine,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.brandContainer}>
          <Text style={styles.brandTitle}>AURA STYLIST</Text>
          <Text style={styles.subTitle}>Autonomous Outfit Architecture • Blend</Text>
        </View>

        <View style={styles.statusGroup}>
          <View
            style={[
              styles.statusBadge,
              { borderColor: isBackendHealthy ? '#065F46' : '#991B1B' },
            ]}
          >
            <View
              style={[
                styles.statusDot,
                { backgroundColor: isBackendHealthy ? '#10B981' : '#EF4444' },
              ]}
            />
            <Text style={styles.statusText}>
              {isBackendHealthy ? 'Agent Online' : 'Backend Offline'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'studio' && styles.activeTab]}
          onPress={() => setActiveTab('studio')}
        >
          <Text style={[styles.tabText, activeTab === 'studio' && styles.activeTabText]}>
            Studio
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'trace' && styles.activeTab]}
          onPress={() => setActiveTab('trace')}
        >
          <Text style={[styles.tabText, activeTab === 'trace' && styles.activeTabText]}>
            Agent Feed
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'outfit' && styles.activeTab]}
          onPress={() => setActiveTab('outfit')}
        >
          <Text style={[styles.tabText, activeTab === 'outfit' && styles.activeTabText]}>
            Outfit {itemCount > 0 ? `(${itemCount})` : ''}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'blend' && styles.activeTab]}
          onPress={() => setActiveTab('blend')}
        >
          <Text style={[styles.tabText, activeTab === 'blend' && styles.activeTabText]}>
            Blend
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0F1318',
    paddingTop: 48,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1F2937',
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  brandContainer: {
    flex: 1,
  },
  brandTitle: {
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: 2,
    color: '#E5B869', // Champagne Gold
  },
  subTitle: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 2,
    letterSpacing: 0.3,
  },
  statusGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#121820',
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 10,
    color: '#E2E8F0',
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#151C24',
    borderRadius: 10,
    padding: 3,
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#E5B869',
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  activeTabText: {
    color: '#0F1318',
    fontWeight: '800',
  },
});
