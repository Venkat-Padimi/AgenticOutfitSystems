import React, { useState, useEffect } from 'react';
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
import { assembleOutfit, submitUserFeedback, getApiBaseUrl } from '../api/client';

interface StylistScreenProps {
  outfit: OutfitRecommendation | null;
  onOutfitGenerated: (outfit: OutfitRecommendation) => void;
  onNavigateToTrace: () => void;
}

const AGENT_LOADING_STAGES = [
  'Goal Understanding: Analyzing occasion, vibe & constraints...',
  'Task Decomposition: Creating category budget allocation...',
  'Tool Execution: Querying shopping catalogs for candidate items...',
  'Constraint Evaluation: Checking budget ceilings and size availability...',
  'Self-Repair Loop: Resolving detected conflicts and replanning...',
  'Synthesizing AI Stylist rationale and ensemble harmony...',
];

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
  const [colorPref, setColorPref] = useState('Navy, White, Tan');

  const [isLoading, setIsLoading] = useState(false);
  const [loadingStageIndex, setLoadingStageIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<(() => Promise<void>) | null>(null);

  const [feedbackText, setFeedbackText] = useState('');
  const [critiqueItemId, setCritiqueItemId] = useState<string | null>(null);
  const [critiqueItemTitle, setCritiqueItemTitle] = useState<string | null>(null);

  // Form validation errors
  const [formErrors, setFormErrors] = useState<{ occasion?: string; budget?: string }>({});

  // Cycle through loading stages during execution
  useEffect(() => {
    let interval: any;
    if (isLoading) {
      setLoadingStageIndex(0);
      interval = setInterval(() => {
        setLoadingStageIndex((prev) => (prev + 1) % AGENT_LOADING_STAGES.length);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const validateForm = (): boolean => {
    const errors: { occasion?: string; budget?: string } = {};
    if (!occasion || occasion.trim().length < 3) {
      errors.occasion = 'Occasion must be at least 3 characters.';
    }
    const numBudget = parseFloat(budget);
    if (isNaN(numBudget) || numBudget < 500) {
      errors.budget = 'Budget must be at least ₹500 for complete outfit generation.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCustomAssemble = async () => {
    if (!validateForm()) return;
    setErrorMessage(null);
    setIsLoading(true);

    const action = async () => {
      const parsedColors = colorPref
        ? colorPref.split(',').map((c) => c.trim()).filter(Boolean)
        : undefined;

      const res = await assembleOutfit({
        occasion: occasion.trim(),
        theme: theme.trim() || 'Smart Casual',
        gender,
        budget_inr: parseFloat(budget),
        sizes: {
          top: topSize.trim() || 'M',
          bottom: bottomSize.trim() || '32',
          shoes: shoeSize.trim() || 'UK 9',
        },
        color_preferences: parsedColors,
      });
      onOutfitGenerated(res);
    };

    setLastAction(() => action);

    try {
      await action();
    } catch (err: any) {
      setErrorMessage(err?.message || 'Agent failed to assemble outfit.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerPreset = async (scenario: 'scenario_1' | 'scenario_2' | 'ethnic_demo') => {
    setErrorMessage(null);
    setIsLoading(true);

    const action = async () => {
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
    };

    setLastAction(() => action);

    try {
      await action();
    } catch (err: any) {
      setErrorMessage(err?.message || 'Preset execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!outfit) return;
    setErrorMessage(null);
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
      setCritiqueItemTitle(null);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Replanning failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    if (lastAction) {
      setErrorMessage(null);
      setIsLoading(true);
      try {
        await lastAction();
      } catch (err: any) {
        setErrorMessage(err?.message || 'Retry failed.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const isGeminiEngine = outfit?.orchestration_engine === 'gemini';
  const isFallbackEngine = outfit?.orchestration_engine === 'deterministic_fallback';
  const isLiveShopping = outfit?.data_source_mode === 'live_verified';
  const isControlledFixture = outfit?.data_source_mode === 'controlled_fixture';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Error Alert Banner */}
      {errorMessage && (
        <View style={styles.errorBanner}>
          <View style={styles.errorTextRow}>
            <Text style={styles.errorIcon}>⚠️</Text>
            <View style={styles.errorTextContainer}>
              <Text style={styles.errorTitle}>Agent Execution Error</Text>
              <Text style={styles.errorDesc}>{errorMessage}</Text>
            </View>
          </View>
          <View style={styles.errorActionRow}>
            <TouchableOpacity style={styles.retryBtn} onPress={handleRetry} disabled={isLoading}>
              <Text style={styles.retryBtnText}>↻ Retry Request</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.dismissBtn}
              onPress={() => setErrorMessage(null)}
            >
              <Text style={styles.dismissBtnText}>Dismiss</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Case Study Quick Scenarios */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionHeader}>Case Study Benchmark Scenarios</Text>
        <Text style={styles.sectionSub}>
          One-click repeatable scenarios for the Engineering College Agentic AI evaluation:
        </Text>

        <TouchableOpacity
          style={styles.scenarioBtn}
          onPress={() => handleTriggerPreset('scenario_2')}
          disabled={isLoading}
        >
          <View style={styles.scenarioBtnTop}>
            <Text style={styles.scenarioTitle}>⚡ Scenario 2: Budget Overrun & Autonomous Replan</Text>
            <View style={styles.replanPill}>
              <Text style={styles.replanPillText}>Self-Repair</Text>
            </View>
          </View>
          <Text style={styles.scenarioDesc}>
            Agent hits ₹5,000 budget ceiling with luxury blazer, detects violation, and executes autonomous self-repair replan.
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
        <Text style={styles.sectionSub}>Configure constraints for the agent orchestrator:</Text>

        <Text style={styles.inputLabel}>Occasion *</Text>
        <TextInput
          style={[styles.input, formErrors.occasion && styles.inputError]}
          value={occasion}
          onChangeText={(v) => {
            setOccasion(v);
            if (formErrors.occasion) setFormErrors((p) => ({ ...p, occasion: undefined }));
          }}
          placeholder="e.g. College Farewell, Conference, Sangeet"
          placeholderTextColor="#64748B"
        />
        {formErrors.occasion && (
          <Text style={styles.fieldErrorText}>{formErrors.occasion}</Text>
        )}

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
                <Text
                  style={[styles.genderBtnText, gender === 'men' && styles.genderBtnTextActive]}
                >
                  Men
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.genderBtn, gender === 'women' && styles.genderBtnActive]}
                onPress={() => setGender('women')}
              >
                <Text
                  style={[styles.genderBtnText, gender === 'women' && styles.genderBtnTextActive]}
                >
                  Women
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.flex1}>
            <Text style={styles.inputLabel}>Budget (₹ INR) *</Text>
            <TextInput
              style={[styles.input, formErrors.budget && styles.inputError]}
              value={budget}
              onChangeText={(v) => {
                setBudget(v);
                if (formErrors.budget) setFormErrors((p) => ({ ...p, budget: undefined }));
              }}
              keyboardType="numeric"
              placeholderTextColor="#64748B"
            />
            {formErrors.budget && (
              <Text style={styles.fieldErrorText}>{formErrors.budget}</Text>
            )}
          </View>
        </View>

        <View style={styles.sizeSection}>
          <Text style={styles.inputLabel}>Sizes (Top / Bottom / Shoes)</Text>
          <View style={styles.sizeInputRow}>
            <View style={styles.sizeInputWrapper}>
              <Text style={styles.sizeSubLabel}>Top</Text>
              <TextInput style={styles.sizeInput} value={topSize} onChangeText={setTopSize} />
            </View>
            <View style={styles.sizeInputWrapper}>
              <Text style={styles.sizeSubLabel}>Bottom</Text>
              <TextInput style={styles.sizeInput} value={bottomSize} onChangeText={setBottomSize} />
            </View>
            <View style={styles.sizeInputWrapper}>
              <Text style={styles.sizeSubLabel}>Shoes</Text>
              <TextInput style={styles.sizeInput} value={shoeSize} onChangeText={setShoeSize} />
            </View>
          </View>
        </View>

        <Text style={styles.inputLabel}>Color Palette / Aesthetic Preferences</Text>
        <TextInput
          style={styles.input}
          value={colorPref}
          onChangeText={setColorPref}
          placeholder="e.g. Navy, White, Tan"
          placeholderTextColor="#64748B"
        />

        <TouchableOpacity
          style={[styles.assembleBtn, isLoading && styles.assembleBtnDisabled]}
          onPress={handleCustomAssemble}
          disabled={isLoading}
        >
          {isLoading ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator color="#0F1318" size="small" />
              <Text style={styles.assembleBtnText}>Agent Synthesizing Ensemble...</Text>
            </View>
          ) : (
            <Text style={styles.assembleBtnText}>✨ Trigger Autonomous Agent Assembly</Text>
          )}
        </TouchableOpacity>

        {/* Live Loading Stage Description */}
        {isLoading && (
          <View style={styles.loadingStageCard}>
            <Text style={styles.loadingStageTitle}>AGENT ACTIVE REASONING:</Text>
            <Text style={styles.loadingStageText}>
              {AGENT_LOADING_STAGES[loadingStageIndex]}
            </Text>
          </View>
        )}
      </View>

      {/* Recommended Outfit Showcase */}
      {outfit ? (
        <View style={styles.outfitSection}>
          <View style={styles.outfitHeaderCard}>
            {/* Engine & Source Badges */}
            <View style={styles.badgeBannerRow}>
              <View
                style={[
                  styles.enginePill,
                  { backgroundColor: isFallbackEngine ? '#78350F' : '#4C1D95' },
                ]}
              >
                <Text style={styles.enginePillText}>
                  {isFallbackEngine ? '⚙️ Deterministic Fallback' : '✨ Gemini 3.5 AI'}
                </Text>
              </View>

              <View
                style={[
                  styles.provenancePill,
                  { backgroundColor: isLiveShopping ? '#065F46' : '#1E293B' },
                ]}
              >
                <Text style={styles.provenancePillText}>
                  {isLiveShopping ? '🟢 Live Shopping' : isControlledFixture ? '🟠 Test Fixture' : '⚡ Cached'}
                </Text>
              </View>
            </View>

            <View style={styles.budgetStatusRow}>
              <Text style={styles.outfitTotalHeading}>
                ₹{outfit.total_price_inr.toLocaleString('en-IN')}
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

            {outfit.tradeoffs_considered && outfit.tradeoffs_considered.length > 0 && (
              <View style={styles.tradeoffBox}>
                <Text style={styles.tradeoffTitle}>Trade-offs Considered:</Text>
                {outfit.tradeoffs_considered.map((t, i) => (
                  <Text key={i} style={styles.tradeoffItem}>• {t}</Text>
                ))}
              </View>
            )}

            <TouchableOpacity style={styles.viewTraceBtn} onPress={onNavigateToTrace}>
              <Text style={styles.viewTraceBtnText}>
                🔍 View {outfit.trace_steps.length} Agent Reasoning Steps & Tool Telemetry →
              </Text>
            </TouchableOpacity>
          </View>

          {/* Feedback & Replan Input */}
          <View style={styles.feedbackCard}>
            <Text style={styles.feedbackTitle}>Human-in-the-Loop Critique & Replanning</Text>
            <Text style={styles.feedbackSub}>
              {critiqueItemTitle
                ? `Critiquing: "${critiqueItemTitle}". Tell the agent what to swap:`
                : 'Guide the agent to refine or swap any component:'}
            </Text>
            <TextInput
              style={styles.input}
              value={feedbackText}
              onChangeText={setFeedbackText}
              placeholder="e.g. 'Swap loafers for clean white court sneakers' or 'Lower the price'"
              placeholderTextColor="#64748B"
            />
            <View style={styles.critiqueActionRow}>
              <TouchableOpacity
                style={[styles.feedbackBtn, isLoading && styles.buttonDisabled]}
                onPress={handleSendFeedback}
                disabled={isLoading}
              >
                <Text style={styles.feedbackBtnText}>Instruct Agent to Replan</Text>
              </TouchableOpacity>
              {critiqueItemId && (
                <TouchableOpacity
                  style={styles.cancelCritiqueBtn}
                  onPress={() => {
                    setCritiqueItemId(null);
                    setCritiqueItemTitle(null);
                    setFeedbackText('');
                  }}
                >
                  <Text style={styles.cancelCritiqueBtnText}>Clear Selection</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>

          {/* Items */}
          <Text style={styles.itemsHeader}>Verified Ensemble Pieces ({outfit.items.length})</Text>
          {outfit.items.map((item, idx) => (
            <ProductCard
              key={idx}
              item={item}
              onCritique={(target) => {
                setCritiqueItemId(target.id);
                setCritiqueItemTitle(target.title);
                setFeedbackText(`Swap ${target.title} for something more casual/affordable`);
              }}
            />
          ))}
        </View>
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>✨</Text>
          <Text style={styles.emptyTitle}>Ready to Assemble Your Ensemble</Text>
          <Text style={styles.emptySub}>
            Select a benchmark scenario above or customize your occasion and budget to experience
            autonomous multi-tool agentic outfit styling.
          </Text>
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
  errorBanner: {
    backgroundColor: '#450A0A',
    borderColor: '#991B1B',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  errorTextRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 10,
  },
  errorIcon: {
    fontSize: 20,
  },
  errorTextContainer: {
    flex: 1,
  },
  errorTitle: {
    color: '#F87171',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 2,
  },
  errorDesc: {
    color: '#FECACA',
    fontSize: 12,
    lineHeight: 16,
  },
  errorActionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  retryBtn: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  retryBtnText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  dismissBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  dismissBtnText: {
    color: '#CBD5E1',
    fontSize: 11,
    fontWeight: '600',
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
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  sectionSub: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 12,
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
    fontWeight: '700',
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
    marginBottom: 10,
  },
  inputError: {
    borderColor: '#EF4444',
  },
  fieldErrorText: {
    color: '#EF4444',
    fontSize: 10,
    marginTop: -6,
    marginBottom: 8,
    fontWeight: '600',
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
    marginBottom: 10,
  },
  genderBtn: {
    flex: 1,
    backgroundColor: '#0B0F14',
    paddingVertical: 9,
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
    marginBottom: 12,
  },
  sizeInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  sizeInputWrapper: {
    flex: 1,
  },
  sizeSubLabel: {
    color: '#64748B',
    fontSize: 9,
    marginBottom: 2,
    textAlign: 'center',
    fontWeight: '600',
  },
  sizeInput: {
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
    marginTop: 4,
  },
  assembleBtnDisabled: {
    opacity: 0.7,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  assembleBtnText: {
    color: '#0F1318',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  loadingStageCard: {
    backgroundColor: '#1E182A',
    borderColor: '#6D28D9',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
  },
  loadingStageTitle: {
    color: '#A78BFA',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  loadingStageText: {
    color: '#EDE9FE',
    fontSize: 11,
    lineHeight: 15,
  },
  outfitSection: {
    marginTop: 4,
  },
  outfitHeaderCard: {
    backgroundColor: '#121820',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  badgeBannerRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
    flexWrap: 'wrap',
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
  budgetStatusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  outfitTotalHeading: {
    color: '#FFFFFF',
    fontSize: 24,
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
    marginBottom: 10,
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
  tradeoffBox: {
    backgroundColor: '#0B0F14',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  tradeoffTitle: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '700',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  tradeoffItem: {
    color: '#CBD5E1',
    fontSize: 11,
    lineHeight: 16,
    marginBottom: 2,
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
    fontWeight: '800',
    marginBottom: 2,
  },
  feedbackSub: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 10,
  },
  critiqueActionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  feedbackBtn: {
    flex: 2,
    backgroundColor: '#38BDF8',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  cancelCritiqueBtn: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  cancelCritiqueBtnText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  feedbackBtnText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '800',
  },
  itemsHeader: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  emptyCard: {
    backgroundColor: '#121820',
    borderRadius: 14,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  emptyIcon: {
    fontSize: 36,
    marginBottom: 10,
  },
  emptyTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 6,
  },
  emptySub: {
    color: '#94A3B8',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});
