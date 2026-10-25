import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { OutfitRecommendation, ProductItem } from '../types';
import { ProductCard } from '../components/ProductCard';
import { assembleOutfit, submitUserFeedback } from '../api/client';

interface StylistScreenProps {
  outfit: OutfitRecommendation | null;
  onOutfitGenerated: (outfit: OutfitRecommendation) => void;
  onNavigateToTrace: () => void;
}

export const StylistScreen: React.FC<StylistScreenProps> = ({
  outfit,
  onOutfitGenerated,
  onNavigateToTrace,
}) => {
  const [occasion, setOccasion] = useState('College Farewell Party');
  const [theme, setTheme] = useState('Minimalist Smart Casual');
  const [gender, setGender] = useState<'men' | 'women'>('men');
  const [budget, setBudget] = useState('5000');
  const [topSize, setTopSize] = useState('M');
  const [bottomSize, setBottomSize] = useState('32');
  const [shoeSize, setShoeSize] = useState('UK 9');
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [critiqueItemId, setCritiqueItemId] = useState<string | null>(null);

  // Preset demo triggers matching Engineering Case Study Scenarios
  const handleTriggerPreset = async (scenario: 'scenario_1' | 'scenario_2' | 'ethnic_demo') => {
    setIsLoading(true);
    try {
      if (scenario === 'scenario_2') {
        // Scenario 2: Forced Budget Overrun -> Autonomous Replan
        setOccasion('College Farewell');
        setTheme('Smart Casual');
        setGender('men');
        setBudget('5000');
        const res = await assembleOutfit({
          occasion: 'College Farewell',
          theme: 'Smart Casual',
          gender: 'men',
          budget_inr: 5000,
          force_test_fixture: 'budget_overrun_scenario',
        });
        onOutfitGenerated(res);
      } else if (scenario === 'scenario_1') {
        setOccasion('Tech Fest Keynote');
        setTheme('Minimalist Smart Casual');
        setGender('men');
        setBudget('6000');
        const res = await assembleOutfit({
          occasion: 'Tech Fest Keynote',
          theme: 'Minimalist Smart Casual',
          gender: 'men',
          budget_inr: 6000,
        });
        onOutfitGenerated(res);
      } else {
        setOccasion('Diwali Sangeet Gala');
        setTheme('Royal Festive Chic');
        setGender('women');
        setBudget('3500');
        const res = await assembleOutfit({
          occasion: 'Diwali Sangeet Gala',
          theme: 'Royal Festive Chic',
          gender: 'women',
          budget_inr: 3500,
        });
        onOutfitGenerated(res);
      }
    } catch (e) {
      console.error('Assembly error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCustomAssemble = async () => {
    setIsLoading(true);
    try {
      const res = await assembleOutfit({
        occasion,
        theme,
        gender,
        budget_inr: parseFloat(budget) || 5000,
        sizes: { top: topSize, bottom: bottomSize, shoes: shoeSize },
      });
      onOutfitGenerated(res);
    } catch (e) {
      console.error('Custom assembly error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!outfit) return;
    setIsLoading(true);
    try {
      const updated = await submitUserFeedback({
        outfit_id: outfit.outfit_id,
        accepted: false,
        rejected_item_ids: critiqueItemId ? [critiqueItemId] : [],
        feedback_text: feedbackText || 'Swap item with casual sneakers',
      });
      onOutfitGenerated(updated);
      setFeedbackText('');
      setCritiqueItemId(null);
    } catch (e) {
      console.error('Feedback error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Case Study Quick Scenarios */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionHeader}>Case Study Quick Scenarios</Text>
        <Text style={styles.sectionSub}>
          One-click repeatable benchmarks designed for engineering college demonstration:
        </Text>

        <TouchableOpacity
          style={styles.scenarioBtn}
          onPress={() => handleTriggerPreset('scenario_2')}
          disabled={isLoading}
        >
          <View style={styles.scenarioBtnTop}>
            <Text style={styles.scenarioTitle}>⚡ Scenario 2: Budget Overrun & Autonomous Replan</Text>
            <View style={styles.replanPill}>
              <Text style={styles.replanPillText}>Self-Repair Demo</Text>
            </View>
          </View>
          <Text style={styles.scenarioDesc}>
            Agent encounters luxury blazer breaking ₹5,000 budget, catches violation, swaps item, and satisfies constraints.
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.scenarioBtn}
          onPress={() => handleTriggerPreset('scenario_1')}
          disabled={isLoading}
        >
          <Text style={styles.scenarioTitle}>🎯 Scenario 1: Standard Themed Look (₹6,000 Budget)</Text>
          <Text style={styles.scenarioDesc}>
            Smart casual blazer, oxford shirt, chinos, and handcrafted leather loafers.
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.scenarioBtn}
          onPress={() => handleTriggerPreset('ethnic_demo')}
          disabled={isLoading}
        >
          <Text style={styles.scenarioTitle}>✨ Festive Chic: Women Indo-Western (₹3,500 Budget)</Text>
          <Text style={styles.scenarioDesc}>
            Navy & Champagne Anarkali Kurta Set paired with embellished mojaris.
          </Text>
        </TouchableOpacity>
      </View>

      {/* Parameter Configuration Form */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionHeader}>Customize Parameters</Text>

        <Text style={styles.inputLabel}>Occasion</Text>
        <TextInput
          style={styles.input}
          value={occasion}
          onChangeText={setOccasion}
          placeholder="e.g. College Farewell, Conference, Sangeet"
          placeholderTextColor="#64748B"
        />

        <Text style={styles.inputLabel}>Theme & Vibe</Text>
        <TextInput
          style={styles.input}
          value={theme}
          onChangeText={setTheme}
          placeholder="e.g. Minimalist Smart Casual, Retro Royal"
          placeholderTextColor="#64748B"
        />

        <View style={styles.row}>
          <View style={styles.flex1}>
            <Text style={styles.inputLabel}>Gender</Text>
            <View style={styles.genderRow}>
              <TouchableOpacity
                style={[styles.genderBtn, gender === 'men' && styles.genderBtnActive]}
                onPress={() => setGender('men')}
              >
                <Text style={[styles.genderBtnText, gender === 'men' && styles.genderBtnTextActive]}>
                  Men
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.genderBtn, gender === 'women' && styles.genderBtnActive]}
                onPress={() => setGender('women')}
              >
                <Text style={[styles.genderBtnText, gender === 'women' && styles.genderBtnTextActive]}>
                  Women
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.flex1}>
            <Text style={styles.inputLabel}>Budget (₹ INR)</Text>
            <TextInput
              style={styles.input}
              value={budget}
              onChangeText={setBudget}
              keyboardType="numeric"
              placeholderTextColor="#64748B"
            />
          </View>
        </View>

        <View style={styles.sizeSection}>
          <Text style={styles.inputLabel}>Sizes (Top / Bottom / Shoes)</Text>
          <View style={styles.sizeInputRow}>
            <TextInput style={styles.sizeInput} value={topSize} onChangeText={setTopSize} />
            <TextInput style={styles.sizeInput} value={bottomSize} onChangeText={setBottomSize} />
            <TextInput style={styles.sizeInput} value={shoeSize} onChangeText={setShoeSize} />
          </View>
        </View>

        <TouchableOpacity
          style={styles.assembleBtn}
          onPress={handleCustomAssemble}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#0F1318" />
          ) : (
            <Text style={styles.assembleBtnText}>✨ Trigger Autonomous Agent Assembly</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Recommended Outfit Showcase */}
      {outfit && (
        <View style={styles.outfitSection}>
          <View style={styles.outfitHeaderCard}>
            <View style={styles.budgetStatusRow}>
              <Text style={styles.outfitTotalHeading}>
                Total: ₹{outfit.total_price_inr.toLocaleString('en-IN')}
              </Text>
              <View
                style={[
                  styles.budgetBadge,
                  { backgroundColor: outfit.is_within_budget ? '#065F46' : '#991B1B' },
                ]}
              >
                <Text style={styles.budgetBadgeText}>
                  {outfit.is_within_budget ? '✓ Within Budget' : '⚠️ Over Budget'}
                </Text>
              </View>
            </View>

            <Text style={styles.budgetSubText}>
              Target: ₹{outfit.target_budget_inr.toLocaleString('en-IN')} • Harmony Score: {outfit.harmony_score.toFixed(0)}%
            </Text>

            <View style={styles.rationaleBox}>
              <Text style={styles.rationaleTitle}>Stylist AI Rationale:</Text>
              <Text style={styles.rationaleText}>{outfit.stylist_rationale}</Text>
            </View>

            <TouchableOpacity style={styles.viewTraceBtn} onPress={onNavigateToTrace}>
              <Text style={styles.viewTraceBtnText}>
                🔍 View {outfit.trace_steps.length} Agent Reasoning Steps & Tool Telemetry →
              </Text>
            </TouchableOpacity>
          </View>

          {/* Feedback & Replan Input */}
          <View style={styles.feedbackCard}>
            <Text style={styles.feedbackTitle}>Feedback & Targeted Replanning</Text>
            <Text style={styles.feedbackSub}>
              {critiqueItemId
                ? `Critiquing selected item. What would you like instead?`
                : 'Guide the agent to refine or swap any component:'}
            </Text>
            <TextInput
              style={styles.input}
              value={feedbackText}
              onChangeText={setFeedbackText}
              placeholder="e.g. 'Loafers too formal, swap for white casual court sneakers'"
              placeholderTextColor="#64748B"
            />
            <TouchableOpacity style={styles.feedbackBtn} onPress={handleSendFeedback}>
              <Text style={styles.feedbackBtnText}>Instruct Agent to Replan</Text>
            </TouchableOpacity>
          </View>

          {/* Items */}
          <Text style={styles.itemsHeader}>Verified Ensemble Pieces ({outfit.items.length})</Text>
          {outfit.items.map((item, idx) => (
            <ProductCard
              key={idx}
              item={item}
              onCritique={(target) => {
                setCritiqueItemId(target.id);
                setFeedbackText(`Swap ${target.title} for something more casual`);
              }}
            />
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0D11',
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  sectionCard: {
    backgroundColor: '#121820',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  sectionHeader: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  sectionSub: {
    color: '#94A3B8',
    fontSize: 12,
    marginBottom: 14,
    lineHeight: 16,
  },
  scenarioBtn: {
    backgroundColor: '#17202B',
    padding: 12,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#263445',
  },
  scenarioBtnTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  scenarioTitle: {
    color: '#E5B869',
    fontSize: 13,
    fontWeight: '700',
  },
  replanPill: {
    backgroundColor: '#EC4899',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  replanPillText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '800',
  },
  scenarioDesc: {
    color: '#94A3B8',
    fontSize: 11,
    lineHeight: 15,
  },
  inputLabel: {
    color: '#CBD5E1',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  input: {
    backgroundColor: '#0B0F14',
    color: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#263342',
    fontSize: 13,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  flex1: {
    flex: 1,
  },
  genderRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 12,
  },
  genderBtn: {
    flex: 1,
    backgroundColor: '#0B0F14',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#263342',
  },
  genderBtnActive: {
    backgroundColor: '#E5B869',
    borderColor: '#E5B869',
  },
  genderBtnText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
  },
  genderBtnTextActive: {
    color: '#0F1318',
  },
  sizeSection: {
    marginBottom: 16,
  },
  sizeInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  sizeInput: {
    flex: 1,
    backgroundColor: '#0B0F14',
    color: '#FFFFFF',
    paddingVertical: 8,
    borderRadius: 6,
    textAlign: 'center',
    borderWidth: 1,
    borderColor: '#263342',
    fontSize: 12,
    fontWeight: '700',
  },
  assembleBtn: {
    backgroundColor: '#E5B869',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  assembleBtnText: {
    color: '#0F1318',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  outfitSection: {
    marginTop: 8,
  },
  outfitHeaderCard: {
    backgroundColor: '#121820',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  budgetStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  outfitTotalHeading: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '800',
  },
  budgetBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  budgetBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  budgetSubText: {
    color: '#94A3B8',
    fontSize: 12,
    marginBottom: 12,
  },
  rationaleBox: {
    backgroundColor: '#0B0F14',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#E5B869',
    marginBottom: 12,
  },
  rationaleTitle: {
    color: '#E5B869',
    fontSize: 10,
    fontWeight: '800',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  rationaleText: {
    color: '#E2E8F0',
    fontSize: 12,
    lineHeight: 18,
  },
  viewTraceBtn: {
    backgroundColor: '#1E293B',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  viewTraceBtnText: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '700',
  },
  feedbackCard: {
    backgroundColor: '#151C24',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#263342',
  },
  feedbackTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  feedbackSub: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 10,
  },
  feedbackBtn: {
    backgroundColor: '#38BDF8',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  feedbackBtnText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '700',
  },
  itemsHeader: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
});
