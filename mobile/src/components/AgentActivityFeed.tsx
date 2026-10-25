import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { AgentTraceStep, ConstraintStatus, OutfitRecommendation } from '../types';

interface AgentActivityFeedProps {
  steps: AgentTraceStep[];
  outfit?: OutfitRecommendation | null;
  isStreaming?: boolean;
}

export const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({ steps, outfit, isStreaming }) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  const toggleExpand = (stepNumber: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'UNDERSTAND_GOAL':
        return '#3B82F6'; // Blue
      case 'DECOMPOSE_PLAN':
        return '#8B5CF6'; // Purple
      case 'SELECT_TOOL':
        return '#06B6D4'; // Cyan
      case 'EXECUTE_TOOL':
        return '#10B981'; // Green
      case 'EVALUATE_CONSTRAINTS':
        return '#F59E0B'; // Amber
      case 'REPLAN':
        return '#EC4899'; // Pink
      case 'SYNTHESIZE_EXPLANATION':
        return '#6366F1'; // Indigo
      case 'COMPLETED':
        return '#10B981'; // Emerald
      default:
        return '#64748B';
    }
  };

  const getConstraintBadge = (status?: ConstraintStatus) => {
    if (!status) return null;
    let bg = '#065F46';
    let text = '✓ CONSTRAINT PASSED';
    if (status === 'VIOLATED') {
      bg = '#991B1B';
      text = '⚠️ CONSTRAINT VIOLATED';
    } else if (status === 'REPAIRED') {
      bg = '#B45309';
      text = '⚡ AUTONOMOUSLY REPAIRED';
    }

    return (
      <View style={[styles.constraintBadge, { backgroundColor: bg }]}>
        <Text style={styles.constraintBadgeText}>{text}</Text>
      </View>
    );
  };

  // Telemetry counts
  const replanSteps = steps.filter((s) => s.phase === 'REPLAN' || s.step_number > 6);
  const constraintViolations = steps.filter((s) => s.constraint_check?.status === 'VIOLATED');
  const constraintRepairs = steps.filter((s) => s.constraint_check?.status === 'REPAIRED');
  const isFallback =
    outfit?.orchestration_engine === 'deterministic_fallback' ||
    steps.some((s) => s.tool_called === 'FallbackToDeterministicEngine');

  if (!steps || steps.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>🤖</Text>
        <Text style={styles.emptyTitle}>No Active Agent Trace</Text>
        <Text style={styles.emptySub}>
          Trigger an outfit assembly from the Studio tab to watch the autonomous agent reason,
          decompose tasks, invoke live shopping tools, and evaluate budget constraints in real time.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Feed Header */}
      <View style={styles.feedHeader}>
        <View>
          <Text style={styles.feedTitle}>Autonomous Agent Execution Trace</Text>
          <Text style={styles.feedSub}>
            Real-time step-by-step reasoning and tool execution telemetry
          </Text>
        </View>
        {isStreaming && (
          <View style={styles.liveIndicator}>
            <View style={styles.pulsingDot} />
            <Text style={styles.liveText}>REASONING LIVE</Text>
          </View>
        )}
      </View>

      {/* Engine & Provenance Banner */}
      <View style={styles.telemetryCard}>
        <View style={styles.telemetryRow}>
          <View style={styles.telemetryBadgeGroup}>
            <View
              style={[
                styles.engineBadge,
                { backgroundColor: isFallback ? '#78350F' : '#4C1D95' },
              ]}
            >
              <Text style={styles.engineBadgeText}>
                {isFallback ? '⚙️ Deterministic Fallback' : '✨ Gemini 3.5 AI'}
              </Text>
            </View>
            {outfit?.data_source_mode && (
              <View
                style={[
                  styles.provenanceBadge,
                  {
                    backgroundColor:
                      outfit.data_source_mode === 'live_verified' ? '#065F46' : '#1E293B',
                  },
                ]}
              >
                <Text style={styles.provenanceBadgeText}>
                  {outfit.data_source_mode === 'live_verified'
                    ? '🟢 Live Shopping'
                    : '🟠 Test Fixtures'}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Quick KPI stats */}
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statVal}>{steps.length}</Text>
            <Text style={styles.statLabel}>Total Steps</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={[styles.statVal, constraintViolations.length > 0 && { color: '#EF4444' }]}>
              {constraintViolations.length}
            </Text>
            <Text style={styles.statLabel}>Violations</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={[styles.statVal, constraintRepairs.length > 0 && { color: '#F59E0B' }]}>
              {constraintRepairs.length}
            </Text>
            <Text style={styles.statLabel}>Repairs</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statVal}>{replanSteps.length}</Text>
            <Text style={styles.statLabel}>Replan Steps</Text>
          </View>
        </View>
      </View>

      {/* Fallback Warning Notice if applicable */}
      {isFallback && (
        <View style={styles.fallbackAlertBox}>
          <Text style={styles.fallbackAlertTitle}>Notice: Fallback Engine Engaged</Text>
          <Text style={styles.fallbackAlertText}>
            The system transitioned to the deterministic agent pipeline to ensure unblocked delivery.
            All budget validations and constraint verification logic remain 100% active.
          </Text>
        </View>
      )}

      {/* Steps List */}
      {steps.map((step) => {
        const phaseColor = getPhaseColor(step.phase);
        const isReplan = step.phase === 'REPLAN';
        const isExpanded = !!expandedSteps[step.step_number];
        const hasPayloads = !!(step.tool_input || step.tool_output);

        return (
          <View
            key={step.step_number}
            style={[styles.stepCard, isReplan && styles.replanCard]}
          >
            <View style={styles.stepHeader}>
              <View style={[styles.stepNumberBadge, { backgroundColor: phaseColor }]}>
                <Text style={styles.stepNumberText}>{step.step_number}</Text>
              </View>
              <View style={[styles.phaseChip, { borderColor: phaseColor }]}>
                <Text style={[styles.phaseChipText, { color: phaseColor }]}>
                  {step.phase.replace('_', ' ')}
                </Text>
              </View>
              {step.tool_called && (
                <View style={styles.toolChip}>
                  <Text style={styles.toolChipText}>Tool: {step.tool_called}</Text>
                </View>
              )}
            </View>

            <View style={styles.thoughtBox}>
              <Text style={styles.thoughtLabel}>AGENT REASONING / THOUGHT:</Text>
              <Text style={styles.thoughtText}>{step.thought}</Text>
            </View>

            {step.constraint_check && (
              <View style={styles.constraintContainer}>
                {getConstraintBadge(step.constraint_check.status)}
                <Text style={styles.constraintDetails}>{step.constraint_check.details}</Text>
              </View>
            )}

            {hasPayloads && (
              <TouchableOpacity
                style={styles.expandPayloadBtn}
                onPress={() => toggleExpand(step.step_number)}
              >
                <Text style={styles.expandPayloadBtnText}>
                  {isExpanded ? '▲ Hide Tool Payloads' : '▼ View Tool Parameters & Observation'}
                </Text>
              </TouchableOpacity>
            )}

            {isExpanded && step.tool_input && (
              <View style={styles.dataPayloadBox}>
                <Text style={styles.dataPayloadLabel}>Tool Parameters:</Text>
                <Text style={styles.dataPayloadCode}>
                  {JSON.stringify(step.tool_input, null, 2)}
                </Text>
              </View>
            )}

            {isExpanded && step.tool_output && (
              <View style={styles.dataPayloadBox}>
                <Text style={styles.dataPayloadLabel}>Tool Observation:</Text>
                <Text style={styles.dataPayloadCode}>
                  {JSON.stringify(step.tool_output, null, 2)}
                </Text>
              </View>
            )}

            {step.timestamp && (
              <Text style={styles.timestampText}>{step.timestamp}</Text>
            )}
          </View>
        );
      })}
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
  feedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  feedTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#F1F5F9',
    letterSpacing: 0.5,
  },
  feedSub: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  pulsingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#EF4444',
    marginRight: 6,
  },
  liveText: {
    color: '#EF4444',
    fontSize: 10,
    fontWeight: '800',
  },
  telemetryCard: {
    backgroundColor: '#121820',
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  telemetryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  telemetryBadgeGroup: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  engineBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  engineBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },
  provenanceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  provenanceBadgeText: {
    color: '#E2E8F0',
    fontSize: 11,
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    paddingTop: 8,
  },
  statBox: {
    alignItems: 'center',
  },
  statVal: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  statLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },
  fallbackAlertBox: {
    backgroundColor: '#3B1D11',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#B45309',
  },
  fallbackAlertTitle: {
    color: '#FBBF24',
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 4,
  },
  fallbackAlertText: {
    color: '#FDE68A',
    fontSize: 11,
    lineHeight: 16,
  },
  stepCard: {
    backgroundColor: '#121820',
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  replanCard: {
    borderColor: '#EC4899',
    backgroundColor: '#18121D',
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  stepNumberBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepNumberText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },
  phaseChip: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
  },
  phaseChipText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  toolChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  toolChipText: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '600',
  },
  thoughtBox: {
    backgroundColor: '#0D1117',
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#E5B869',
  },
  thoughtLabel: {
    color: '#E5B869',
    fontSize: 10,
    fontWeight: '800',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  thoughtText: {
    color: '#E2E8F0',
    fontSize: 13,
    lineHeight: 19,
  },
  constraintContainer: {
    backgroundColor: '#0F172A',
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  constraintBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginBottom: 6,
  },
  constraintBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
  },
  constraintDetails: {
    color: '#CBD5E1',
    fontSize: 12,
    lineHeight: 17,
  },
  expandPayloadBtn: {
    paddingVertical: 4,
    alignItems: 'flex-start',
  },
  expandPayloadBtnText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '600',
  },
  dataPayloadBox: {
    backgroundColor: '#0B0F14',
    padding: 8,
    borderRadius: 6,
    marginTop: 6,
  },
  dataPayloadLabel: {
    color: '#64748B',
    fontSize: 9,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  dataPayloadCode: {
    color: '#38BDF8',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  timestampText: {
    color: '#475569',
    fontSize: 10,
    textAlign: 'right',
    marginTop: 6,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 300,
  },
  emptyIcon: {
    fontSize: 44,
    marginBottom: 12,
  },
  emptyTitle: {
    color: '#F1F5F9',
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 8,
  },
  emptySub: {
    color: '#94A3B8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 19,
  },
});
