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
  const [isAddingFriend, setIsAddingFriend] = useState(false);
  const [friendName, setFriendName] = useState('Sneha');
  const [friendBudget, setFriendBudget] = useState('3500');
  const [friendStyle, setFriendStyle] = useState('Indo-Western fusion');
  const [friendGender, setFriendGender] = useState<'men' | 'women'>('women');
  const [showAddFriend, setShowAddFriend] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleCoordinate = async () => {
    if (!session) return;
    setErrorMessage(null);
    setIsCoordinating(true);
    try {
      const updated = await coordinateBlend(session.blend_id);
      onRefreshSession(updated);
    } catch (e: any) {
      setErrorMessage(e?.message || 'Failed to coordinate group outfits.');
    } finally {
      setIsCoordinating(false);
    }
  };

  const handleAddFriend = async () => {
    if (!session) return;
    const numBudget = parseFloat(friendBudget);
    if (!friendName.trim()) {
      setErrorMessage('Friend name is required.');
      return;
    }
    if (isNaN(numBudget) || numBudget < 500) {
      setErrorMessage('Friend budget must be at least ₹500.');
      return;
    }

    setErrorMessage(null);
    setIsAddingFriend(true);
    try {
      const updated = await joinBlend({
        blend_id: session.blend_id,
        member_name: friendName.trim(),
        member_budget_inr: numBudget,
        member_style: friendStyle.trim() || 'Smart Casual',
        member_gender: friendGender,
      });
      onRefreshSession(updated);
      setShowAddFriend(false);
      setFriendName('');
    } catch (e: any) {
      setErrorMessage(e?.message || 'Failed to add friend to blend room.');
    } finally {
      setIsAddingFriend(false);
    }
  };

  if (!session) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>👥</Text>
        <Text style={styles.emptyTitle}>Group Styling Studio ("Blend")</Text>
        <Text style={styles.emptySub}>
          Collaborate with friends to build synchronized outfits for festivals, farewells, weddings,
          or trips while respecting each person's unique budget and personal style.
        </Text>
        <TouchableOpacity style={styles.createButton} onPress={onCreateNewRoom}>
          <Text style={styles.createButtonText}>Initialize Blend Room</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Error Banner */}
      {errorMessage && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>⚠️ {errorMessage}</Text>
          <TouchableOpacity onPress={() => setErrorMessage(null)}>
            <Text style={styles.errorDismiss}>Dismiss</Text>
          </TouchableOpacity>
        </View>
      )}

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
            style={[styles.coordinateBtn, isCoordinating && styles.btnDisabled]}
            onPress={handleCoordinate}
            disabled={isCoordinating}
          >
            {isCoordinating ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color="#0F1318" size="small" />
                <Text style={styles.coordinateBtnText}>Harmonizing Outfits...</Text>
              </View>
            ) : (
              <Text style={styles.coordinateBtnText}>⚡ Coordinate Group Outfits</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.addFriendBtn}
            onPress={() => setShowAddFriend(!showAddFriend)}
          >
            <Text style={styles.addFriendBtnText}>
              {showAddFriend ? 'Cancel' : '+ Add Friend'}
            </Text>
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
            placeholder="Friend Name (e.g. Sneha)"
            placeholderTextColor="#64748B"
          />
          <TextInput
            style={styles.input}
            value={friendBudget}
            onChangeText={setFriendBudget}
            placeholder="Personal Budget (₹ INR, min 500)"
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

          <View style={styles.genderSelectRow}>
            <TouchableOpacity
              style={[styles.genderSelectBtn, friendGender === 'women' && styles.genderSelectActive]}
              onPress={() => setFriendGender('women')}
            >
              <Text style={[styles.genderSelectText, friendGender === 'women' && styles.genderSelectTextActive]}>
                Women
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.genderSelectBtn, friendGender === 'men' && styles.genderSelectActive]}
              onPress={() => setFriendGender('men')}
            >
              <Text style={[styles.genderSelectText, friendGender === 'men' && styles.genderSelectTextActive]}>
                Men
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.submitFriendBtn, isAddingFriend && styles.btnDisabled]}
            onPress={handleAddFriend}
            disabled={isAddingFriend}
          >
            {isAddingFriend ? (
              <ActivityIndicator color="#0F1318" size="small" />
            ) : (
              <Text style={styles.submitFriendBtnText}>Add Friend to Room</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Members Outfits */}
      <View style={styles.membersSection}>
        <Text style={styles.membersHeader}>
          Group Members & Coordinated Looks ({session.members.length})
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
                  <View
                    style={[
                      styles.memberBudgetBadge,
                      {
                        backgroundColor: member.recommended_outfit.is_within_budget
                          ? '#065F46'
                          : '#991B1B',
                      },
                    ]}
                  >
                    <Text style={styles.memberBudgetText}>
                      {member.recommended_outfit.is_within_budget
                        ? '✓ Within Budget'
                        : '⚠️ Over Budget'}
                    </Text>
                  </View>
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
    minHeight: 400,
  },
  emptyIcon: {
    fontSize: 44,
    marginBottom: 12,
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
    fontWeight: '800',
    fontSize: 14,
  },
  errorBanner: {
    backgroundColor: '#450A0A',
    borderColor: '#991B1B',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorText: {
    color: '#FECACA',
    fontSize: 12,
    flex: 1,
  },
  errorDismiss: {
    color: '#F87171',
    fontSize: 11,
    fontWeight: '700',
    marginLeft: 8,
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
    marginBottom: 8,
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
    fontWeight: '800',
    letterSpacing: 1,
  },
  cohesionBadge: {
    backgroundColor: '#065F46',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignItems: 'center',
  },
  cohesionScore: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
  },
  cohesionLabel: {
    color: '#A7F3D0',
    fontSize: 8,
    fontWeight: '800',
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
    fontWeight: '600',
  },
  paletteChip: {
    backgroundColor: '#1A2330',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#263342',
  },
  paletteChipText: {
    color: '#CBD5E1',
    fontSize: 11,
    fontWeight: '600',
  },
  summaryBox: {
    backgroundColor: '#0B0F14',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#E5B869',
    marginBottom: 14,
  },
  summaryTitle: {
    color: '#E5B869',
    fontSize: 10,
    fontWeight: '800',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  summaryText: {
    color: '#E2E8F0',
    fontSize: 12,
    lineHeight: 18,
  },
  actionBtnRow: {
    flexDirection: 'row',
    gap: 10,
  },
  coordinateBtn: {
    flex: 3,
    backgroundColor: '#E5B869',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  coordinateBtnText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  addFriendBtn: {
    flex: 2,
    backgroundColor: '#1E293B',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  addFriendBtnText: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700',
  },
  friendForm: {
    backgroundColor: '#151C24',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#263342',
  },
  formTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 10,
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
  genderSelectRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  genderSelectBtn: {
    flex: 1,
    backgroundColor: '#0B0F14',
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#263342',
  },
  genderSelectActive: {
    backgroundColor: '#E5B869',
    borderColor: '#E5B869',
  },
  genderSelectText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '700',
  },
  genderSelectTextActive: {
    color: '#0F1318',
  },
  submitFriendBtn: {
    backgroundColor: '#38BDF8',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  submitFriendBtnText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '800',
  },
  membersSection: {
    marginTop: 4,
  },
  membersHeader: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  memberCard: {
    backgroundColor: '#121820',
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  memberMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  memberName: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
  },
  memberStyle: {
    color: '#94A3B8',
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
    color: '#E2E8F0',
    fontSize: 11,
    fontWeight: '700',
  },
  outfitSubSection: {
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    paddingTop: 12,
  },
  outfitStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  outfitTotal: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  memberBudgetBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  memberBudgetText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  pendingOutfitBox: {
    backgroundColor: '#0D1117',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#1E293B',
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  pendingText: {
    color: '#64748B',
    fontSize: 11,
    textAlign: 'center',
  },
});
