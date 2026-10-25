import React, { useState, useEffect } from 'react';
import { StyleSheet, View, SafeAreaView, ScrollView, Text, TouchableOpacity } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Header } from './src/components/Header';
import { StylistScreen } from './src/screens/StylistScreen';
import { AgentActivityFeed } from './src/components/AgentActivityFeed';
import { BlendView } from './src/components/BlendView';
import { ProductCard } from './src/components/ProductCard';
import { OutfitRecommendation, BlendSession } from './src/types';
import { checkBackendHealth, createBlend, BackendHealthResponse, getApiBaseUrl } from './src/api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState<'studio' | 'trace' | 'outfit' | 'blend'>('studio');
  const [backendHealth, setBackendHealth] = useState<BackendHealthResponse>({ healthy: false });
  const [outfit, setOutfit] = useState<OutfitRecommendation | null>(null);
  const [blendSession, setBlendSession] = useState<BlendSession | null>(null);

  // Periodically check backend health
  useEffect(() => {
    let isMounted = true;
    const pollHealth = async () => {
      const res = await checkBackendHealth();
      if (isMounted) {
        setBackendHealth(res);
      }
    };
    pollHealth();
    const interval = setInterval(pollHealth, 6000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Pre-seed an initial Blend room for instant group demonstration
  useEffect(() => {
    const seedBlend = async () => {
      if (!blendSession && backendHealth.healthy) {
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
          // Backend not ready or blend creation error
        }
      }
    };
    seedBlend();
  }, [backendHealth.healthy]);

  const handleOutfitGenerated = (newOutfit: OutfitRecommendation) => {
    setOutfit(newOutfit);
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

  const isGeminiEngine = outfit?.orchestration_engine === 'gemini';
  const isFallbackEngine = outfit?.orchestration_engine === 'deterministic_fallback';
  const isLive = outfit?.data_source_mode === 'live_verified';
  const isFixture = outfit?.data_source_mode === 'controlled_fixture';

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <View style={styles.container}>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isBackendHealthy={backendHealth.healthy}
          itemCount={outfit?.items.length || 0}
          engine={outfit?.orchestration_engine}
        />

        {activeTab === 'studio' && (
          <StylistScreen
            outfit={outfit}
            onOutfitGenerated={handleOutfitGenerated}
            onNavigateToTrace={() => setActiveTab('trace')}
          />
        )}

        {activeTab === 'trace' && (
          <AgentActivityFeed steps={outfit?.trace_steps || []} outfit={outfit} />
        )}

        {activeTab === 'outfit' && (
          <ScrollView style={styles.tabContent} contentContainerStyle={styles.tabScrollContent}>
            {outfit ? (
              <View>
                <View style={styles.outfitMetaHeader}>
                  <View style={styles.badgeRow}>
                    <View
                      style={[
                        styles.enginePill,
                        { backgroundColor: isFallbackEngine ? '#78350F' : '#4C1D95' },
                      ]}
                    >
                      <Text style={styles.enginePillText}>
                        {isFallbackEngine ? '⚙️ Fallback Engine' : '✨ Gemini 3.5 AI'}
                      </Text>
                    </View>
                    <View
                      style={[
                        styles.provenancePill,
                        { backgroundColor: isLive ? '#065F46' : '#1E293B' },
                      ]}
                    >
                      <Text style={styles.provenancePillText}>
                        {isLive ? '🟢 Live Shopping' : isFixture ? '🟠 Test Fixture' : '⚡ Cached'}
                      </Text>
                    </View>
                  </View>

                  <Text style={styles.outfitMetaTitle}>{outfit.theme}</Text>
                  <Text style={styles.outfitMetaOccasion}>Occasion: {outfit.occasion}</Text>

                  <View style={styles.priceContainer}>
                    <Text style={styles.outfitMetaPrice}>
                      Total: ₹{outfit.total_price_inr.toLocaleString('en-IN')}
                    </Text>
                    <Text style={styles.outfitTargetPrice}>
                      Target: ₹{outfit.target_budget_inr.toLocaleString('en-IN')}
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={styles.inspectTraceBtn}
                    onPress={() => setActiveTab('trace')}
                  >
                    <Text style={styles.inspectTraceBtnText}>
                      🔍 Inspect {outfit.trace_steps.length} Agent Reasoning Steps & Tool Telemetry →
                    </Text>
                  </TouchableOpacity>
                </View>

                {outfit.items.map((item, idx) => (
                  <ProductCard key={idx} item={item} />
                ))}
              </View>
            ) : (
              <View style={styles.emptyCenter}>
                <Text style={styles.emptyIcon}>🛍️</Text>
                <Text style={styles.emptyTitle}>No Outfit Assembled Yet</Text>
                <Text style={styles.emptySub}>
                  Head over to the Studio tab and trigger an autonomous outfit assembly or select a benchmark scenario.
                </Text>
                <TouchableOpacity
                  style={styles.goToStudioBtn}
                  onPress={() => setActiveTab('studio')}
                >
                  <Text style={styles.goToStudioBtnText}>Go to Studio</Text>
                </TouchableOpacity>
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
    borderRadius: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  enginePill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  enginePillText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
  },
  provenancePill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  provenancePillText: {
    color: '#E2E8F0',
    fontSize: 10,
    fontWeight: '700',
  },
  outfitMetaTitle: {
    color: '#E5B869',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 2,
  },
  outfitMetaOccasion: {
    color: '#94A3B8',
    fontSize: 12,
    marginBottom: 8,
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 10,
    marginBottom: 12,
  },
  outfitMetaPrice: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  outfitTargetPrice: {
    color: '#64748B',
    fontSize: 12,
  },
  inspectTraceBtn: {
    backgroundColor: '#1E293B',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  inspectTraceBtnText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '700',
  },
  emptyCenter: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
  },
  emptyIcon: {
    fontSize: 44,
    marginBottom: 12,
  },
  emptyTitle: {
    color: '#F1F5F9',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 8,
  },
  emptySub: {
    color: '#94A3B8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 20,
  },
  goToStudioBtn: {
    backgroundColor: '#E5B869',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  goToStudioBtnText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '800',
  },
});
