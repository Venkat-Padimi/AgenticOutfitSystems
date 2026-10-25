import React, { useState, useEffect } from 'react';
import { StyleSheet, View, SafeAreaView, ScrollView, Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Header } from './src/components/Header';
import { StylistScreen } from './src/screens/StylistScreen';
import { AgentActivityFeed } from './src/components/AgentActivityFeed';
import { BlendView } from './src/components/BlendView';
import { ProductCard } from './src/components/ProductCard';
import { OutfitRecommendation, BlendSession } from './src/types';
import { checkBackendHealth, createBlend } from './src/api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState<'studio' | 'trace' | 'outfit' | 'blend'>('studio');
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);
  const [outfit, setOutfit] = useState<OutfitRecommendation | null>(null);
  const [blendSession, setBlendSession] = useState<BlendSession | null>(null);

  // Periodically check backend health
  useEffect(() => {
    const pollHealth = async () => {
      const res = await checkBackendHealth();
      setIsBackendHealthy(res.healthy);
    };
    pollHealth();
    const interval = setInterval(pollHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Pre-seed an initial Blend room for instant group testing
  useEffect(() => {
    const seedBlend = async () => {
      try {
        const seeded = await createBlend({
          title: 'College Farewell 2026',
          occasion: 'Graduation Gala',
          shared_theme: 'Royal Retro Elegance',
          shared_palette: ['Navy Blue', 'Champagne Gold', 'Ivory'],
          host_name: 'Arjun',
          host_budget_inr: 6000,
          host_gender: 'men',
        });
        setBlendSession(seeded);
      } catch (e) {
        // Backend not ready yet
      }
    };
    seedBlend();
  }, [isBackendHealthy]);

  const handleOutfitGenerated = (newOutfit: OutfitRecommendation) => {
    setOutfit(newOutfit);
    // Switch to outfit or trace tab automatically if user desires
  };

  const handleCreateNewRoom = async () => {
    try {
      const created = await createBlend({
        title: 'Diwali Sangeet 2026',
        occasion: 'Festive Wedding Event',
        shared_theme: 'Royal Ethnic Fusion',
        shared_palette: ['Royal Blue', 'Champagne Gold', 'Blush Peach'],
        host_name: 'Arjun',
        host_budget_inr: 5500,
        host_gender: 'men',
      });
      setBlendSession(created);
    } catch (e) {
      console.error('Create room error:', e);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <View style={styles.container}>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isBackendHealthy={isBackendHealthy}
          itemCount={outfit?.items.length || 0}
        />

        {activeTab === 'studio' && (
          <StylistScreen
            outfit={outfit}
            onOutfitGenerated={handleOutfitGenerated}
            onNavigateToTrace={() => setActiveTab('trace')}
          />
        )}

        {activeTab === 'trace' && (
          <AgentActivityFeed steps={outfit?.trace_steps || []} />
        )}

        {activeTab === 'outfit' && (
          <ScrollView style={styles.tabContent} contentContainerStyle={styles.tabScrollContent}>
            {outfit ? (
              <View>
                <View style={styles.outfitMetaHeader}>
                  <Text style={styles.outfitMetaTitle}>{outfit.theme}</Text>
                  <Text style={styles.outfitMetaOccasion}>Occasion: {outfit.occasion}</Text>
                  <Text style={styles.outfitMetaPrice}>
                    Total: ₹{outfit.total_price_inr.toLocaleString('en-IN')} (Target: ₹{outfit.target_budget_inr.toLocaleString('en-IN')})
                  </Text>
                </View>
                {outfit.items.map((item, idx) => (
                  <ProductCard key={idx} item={item} />
                ))}
              </View>
            ) : (
              <View style={styles.emptyCenter}>
                <Text style={styles.emptyTitle}>No Outfit Assembled Yet</Text>
                <Text style={styles.emptySub}>
                  Head over to the Studio tab and trigger an outfit assembly or choose a case study benchmark scenario!
                </Text>
              </View>
            )}
          </ScrollView>
        )}

        {activeTab === 'blend' && (
          <BlendView
            session={blendSession}
            onRefreshSession={setBlendSession}
            onCreateNewRoom={handleCreateNewRoom}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0A0D11',
  },
  container: {
    flex: 1,
    backgroundColor: '#0A0D11',
  },
  tabContent: {
    flex: 1,
    backgroundColor: '#0A0D11',
  },
  tabScrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  outfitMetaHeader: {
    backgroundColor: '#121820',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  outfitMetaTitle: {
    color: '#E5B869',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 4,
  },
  outfitMetaOccasion: {
    color: '#94A3B8',
    fontSize: 12,
    marginBottom: 6,
  },
  outfitMetaPrice: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  emptyCenter: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    color: '#F1F5F9',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  emptySub: {
    color: '#94A3B8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
  },
});
