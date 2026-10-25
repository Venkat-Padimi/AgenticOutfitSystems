import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { AgentTraceStep, ConstraintStatus } from '../types';

interface AgentActivityFeedProps {
  steps: AgentTraceStep[];
  isStreaming?: boolean;
}

export const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({ steps, isStreaming }) => {
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
      case 'COMPLETED':
        return '#10B981'; // Emerald
      default:
        return '#6B7280';
    }
  };

  const getConstraintBadge = (status?: ConstraintStatus) => {
    if (!status) return null;
    let bg = '#10B981';
    let text = 'PASSED';
    if (status === 'VIOLATED') {
      bg = '#EF4444';
      text = '⚠️ CONSTRAINT VIOLATED';
    } else if (status === 'REPAIRED') {
      bg = '#E5B869';
      text = '✓ AUTONOMOUSLY REPAIRED';
    }

    return (
      <View style={[styles.constraintBadge, { backgroundColor: bg }]}>
        <Text style={styles.constraintBadgeText}>{text}</Text>
      </View>
    );
  };

  if (!steps || steps.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyTitle}>No Active Agent Trace</Text>
        <Text style={styles.emptySub}>
          Trigger an outfit assembly from the Studio tab to watch the autonomous agent reason, query live tools, and validate constraints in real time.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.feedHeader}>
        <Text style={styles.feedTitle}>Autonomous Agent Execution Trace</Text>
        {isStreaming && (
          <View style={styles.liveIndicator}>
            <View style={styles.pulsingDot} />
            <Text style={styles.liveText}>REASONING LIVE</Text>
          </View>
        )}
      </View>

      {steps.map((step, idx) => {
        const phaseColor = getPhaseColor(step.phase);
        const isReplan = step.phase === 'REPLAN';

        return (
          <View key={idx} style={[styles.stepCard, isReplan && styles.replanCard]}>
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
              <Text style={styles.thoughtLabel}>THOUGHT / REASONING:</Text>
              <Text style={styles.thoughtText}>{step.thought}</Text>
            </View>

            {step.constraint_check && (
              <View style={styles.constraintContainer}>
                {getConstraintBadge(step.constraint_check.status)}
                <Text style={styles.constraintDetails}>{step.constraint_check.details}</Text>
              </View>
            )}

            {step.tool_input && (
              <View style={styles.dataPayloadBox}>
                <Text style={styles.dataPayloadLabel}>Tool Parameters:</Text>
                <Text style={styles.dataPayloadCode}>
                  {JSON.stringify(step.tool_input, null, 2)}
                </Text>
              </View>
            )}

            {step.tool_output && (
              <View style={styles.dataPayloadBox}>
                <Text style={styles.dataPayloadLabel}>Tool Observation:</Text>
                <Text style={styles.dataPayloadCode}>
                  {JSON.stringify(step.tool_output, null, 2)}
                </Text>
              </View>
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
    marginBottom: 16,
  },
  feedTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
    letterSpacing: 0.5,
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
    backgroundColor: '#1A121E',
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  stepNumberBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
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
    fontWeight: '700',
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
    lineHeight: 18,
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
  },
  dataPayloadBox: {
    backgroundColor: '#0B0F14',
    padding: 8,
    borderRadius: 6,
    marginTop: 4,
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
    fontSize: 11,
    fontFamily: 'monospace',
  },
  emptyContainer: {
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
