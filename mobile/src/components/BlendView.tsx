import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { BlendSession } from '../types';
import { ProductCard } from './ProductCard';
import { coordinateBlend, joinBlend } from '../api/client';

interface BlendViewProps {
  session: BlendSession | null;
  onRefreshSession: (updated: BlendSession) => void;
  onCreateNewRoom: () => void;
}

export const BlendView: React.FC<BlendViewProps> = ({
  session,
  onRefreshSession,
  onCreateNewRoom,
}) => {
  const [isCoordinating, setIsCoordinating] = useState(false);
  const [friendName, setFriendName] = useState('Sneha');
  const [friendBudget, setFriendBudget] = useState('3500');
  const [friendStyle, setFriendStyle] = useState('Indo-Western fusion');
  const [showAddFriend, setShowAddFriend] = useState(false);

  const handleCoordinate = async () => {
    if (!session) return;
    setIsCoordinating(true);
    try {
      const updated = await coordinateBlend(session.blend_id);
      onRefreshSession(updated);
    } catch (e) {
      console.error('Coordination error:', e);
    } finally {
      setIsCoordinating(false);
    }
  };

  const handleAddFriend = async () => {
    if (!session) return;
    try {
      const updated = await joinBlend({
        blend_id: session.blend_id,
        member_name: friendName,
        member_budget_inr: parseFloat(friendBudget) || 3500,
        member_style: friendStyle,
        member_gender: 'women',
      });
      onRefreshSession(updated);
      setShowAddFriend(false);
    } catch (e) {
      console.error('Failed to join friend:', e);
    }
  };

  if (!session) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyTitle}>Group Styling Studio ("Blend")</Text>
        <Text style={styles.emptySub}>
          Collaborate with friends to build synchronized outfits for festivals, farewells, weddings, or trips while respecting each person's unique budget and style.
        </Text>
        <TouchableOpacity style={styles.createButton} onPress={onCreateNewRoom}>
          <Text style={styles.createButtonText}>Initialize Blend Room</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Blend Room Header Card */}
      <View style={styles.headerCard}>
        <View style={styles.roomBadgeRow}>
          <View style={styles.roomCodeBadge}>
            <Text style={styles.roomCodeText}>ROOM: {session.blend_id.toUpperCase()}</Text>
          </View>
          <View style={styles.cohesionBadge}>
            <Text style={styles.cohesionScore}>
              {session.group_cohesion_score.toFixed(0)}%
            </Text>
            <Text style={styles.cohesionLabel}>COHESION</Text>
          </View>
        </View>

        <Text style={styles.title}>{session.title}</Text>
        <Text style={styles.themeSubtitle}>Theme: {session.shared_theme}</Text>

        <View style={styles.paletteRow}>
          <Text style={styles.paletteLabel}>Color Story:</Text>
          {session.shared_palette.map((color, idx) => (
            <View key={idx} style={styles.paletteChip}>
              <Text style={styles.paletteChipText}>{color}</Text>
            </View>
          ))}
        </View>

        {session.harmonization_summary ? (
          <View style={styles.summaryBox}>
            <Text style={styles.summaryTitle}>Stylist Harmonization Rationale:</Text>
            <Text style={styles.summaryText}>{session.harmonization_summary}</Text>
          </View>
        ) : null}

        <View style={styles.actionBtnRow}>
          <TouchableOpacity
            style={styles.coordinateBtn}
            onPress={handleCoordinate}
            disabled={isCoordinating}
          >
            {isCoordinating ? (
              <ActivityIndicator color="#0F1318" size="small" />
            ) : (
              <Text style={styles.coordinateBtnText}>⚡ Coordinate Group Outfits</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.addFriendBtn}
            onPress={() => setShowAddFriend(!showAddFriend)}
          >
            <Text style={styles.addFriendBtnText}>+ Add Friend</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Add Friend Accordion */}
      {showAddFriend && (
        <View style={styles.friendForm}>
          <Text style={styles.formTitle}>Invite Friend to Blend</Text>
          <TextInput
            style={styles.input}
            value={friendName}
            onChangeText={setFriendName}
            placeholder="Friend Name"
            placeholderTextColor="#64748B"
          />
          <TextInput
            style={styles.input}
            value={friendBudget}
            onChangeText={setFriendBudget}
            placeholder="Personal Budget (₹ INR)"
            placeholderTextColor="#64748B"
            keyboardType="numeric"
          />
          <TextInput
            style={styles.input}
            value={friendStyle}
            onChangeText={setFriendStyle}
            placeholder="Style Preference (e.g. Indo-Western chic)"
            placeholderTextColor="#64748B"
          />
          <TouchableOpacity style={styles.submitFriendBtn} onPress={handleAddFriend}>
            <Text style={styles.submitFriendBtnText}>Add Friend to Room</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Members Outfits */}
      <View style={styles.membersSection}>
        <Text style={styles.membersHeader}>
          Group Members & Looks ({session.members.length})
        </Text>

        {session.members.map((member, idx) => (
          <View key={idx} style={styles.memberCard}>
            <View style={styles.memberMetaRow}>
              <View>
                <Text style={styles.memberName}>{member.display_name}</Text>
                <Text style={styles.memberStyle}>
                  {member.gender.toUpperCase()} • {member.personal_style}
                </Text>
              </View>
              <View style={styles.budgetPill}>
                <Text style={styles.budgetPillText}>
                  Budget: ₹{member.budget_inr.toLocaleString('en-IN')}
                </Text>
              </View>
            </View>

            {member.recommended_outfit ? (
              <View style={styles.outfitSubSection}>
                <View style={styles.outfitStatsRow}>
                  <Text style={styles.outfitTotal}>
                    Total: ₹{member.recommended_outfit.total_price_inr.toLocaleString('en-IN')}
                  </Text>
                  <Text style={styles.outfitStatus}>
                    {member.recommended_outfit.is_within_budget ? '✓ Within Budget' : '⚠️ Over Budget'}
                  </Text>
                </View>

                {member.recommended_outfit.items.map((item, itemIdx) => (
                  <ProductCard key={itemIdx} item={item} />
                ))}
              </View>
            ) : (
              <View style={styles.pendingOutfitBox}>
                <Text style={styles.pendingText}>
                  Outfit awaiting coordination. Tap 'Coordinate Group Outfits' above.
                </Text>
              </View>
            )}
          </View>
        ))}
      </View>
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
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    color: '#F1F5F9',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptySub: {
    color: '#94A3B8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  createButton: {
    backgroundColor: '#E5B869',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  createButtonText: {
    color: '#0F1318',
    fontWeight: '700',
    fontSize: 14,
  },
  headerCard: {
    backgroundColor: '#121820',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  roomBadgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  roomCodeBadge: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  roomCodeText: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '700',
  },
  cohesionBadge: {
    flexDirection: 'row',
    alignItems: 'baseline',
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#10B981',
  },
  cohesionScore: {
    color: '#10B981',
    fontSize: 14,
    fontWeight: '800',
    marginRight: 4,
  },
  cohesionLabel: {
    color: '#10B981',
    fontSize: 9,
    fontWeight: '700',
  },
  title: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '800',
    marginBottom: 4,
  },
  themeSubtitle: {
    color: '#E5B869',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 12,
  },
  paletteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 12,
  },
  paletteLabel: {
    color: '#64748B',
    fontSize: 11,
    marginRight: 4,
  },
  paletteChip: {
    backgroundColor: '#1A232E',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#2D3A4B',
  },
  paletteChipText: {
    color: '#E2E8F0',
    fontSize: 11,
    fontWeight: '600',
  },
  summaryBox: {
    backgroundColor: '#0F151D',
    padding: 10,
    borderRadius: 8,
    marginBottom: 14,
    borderLeftWidth: 3,
    borderLeftColor: '#10B981',
  },
  summaryTitle: {
    color: '#10B981',
    fontSize: 10,
    fontWeight: '700',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  summaryText: {
    color: '#CBD5E1',
    fontSize: 12,
    lineHeight: 18,
  },
  actionBtnRow: {
    flexDirection: 'row',
    gap: 10,
  },
  coordinateBtn: {
    flex: 2,
    backgroundColor: '#E5B869',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  coordinateBtnText: {
    color: '#0F1318',
    fontWeight: '800',
    fontSize: 13,
  },
  addFriendBtn: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  addFriendBtnText: {
    color: '#E2E8F0',
    fontWeight: '600',
    fontSize: 12,
  },
  friendForm: {
    backgroundColor: '#151C24',
    padding: 14,
    borderRadius: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#263342',
  },
  formTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 10,
  },
  input: {
    backgroundColor: '#0B0F14',
    color: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#263342',
    fontSize: 12,
    marginBottom: 8,
  },
  submitFriendBtn: {
    backgroundColor: '#10B981',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  submitFriendBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 12,
  },
  membersSection: {
    marginTop: 8,
  },
  membersHeader: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  memberCard: {
    backgroundColor: '#121820',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  memberMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  memberName: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  memberStyle: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  budgetPill: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  budgetPillText: {
    color: '#E5B869',
    fontSize: 11,
    fontWeight: '700',
  },
  outfitSubSection: {
    marginTop: 6,
  },
  outfitStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    marginBottom: 12,
  },
  outfitTotal: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '700',
  },
  outfitStatus: {
    color: '#10B981',
    fontSize: 12,
    fontWeight: '600',
  },
  pendingOutfitBox: {
    backgroundColor: '#0B0F14',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  pendingText: {
    color: '#64748B',
    fontSize: 12,
    textAlign: 'center',
  },
});
