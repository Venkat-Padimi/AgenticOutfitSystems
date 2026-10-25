import React from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, Linking } from 'react-native';
import { ProductItem } from '../types';

interface ProductCardProps {
  item: ProductItem;
  onCritique?: (item: ProductItem) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ item, onCritique }) => {
  const handleOpenStore = () => {
    if (item.product_url) {
      Linking.openURL(item.product_url);
    }
  };

  const isVerifiedLive = item.data_source === 'live_verified';

  return (
    <View style={styles.card}>
      <View style={styles.imageContainer}>
        <Image source={{ uri: item.image_url }} style={styles.image} resizeMode="cover" />
        <View style={styles.badgeRow}>
          <View style={styles.merchantBadge}>
            <Text style={styles.merchantText}>{item.merchant}</Text>
          </View>
          <View
            style={[
              styles.sourceBadge,
              { backgroundColor: isVerifiedLive ? '#065F46' : '#1E3A5F' },
            ]}
          >
            <Text style={styles.sourceText}>
              {isVerifiedLive ? '✓ Live Verified' : '⟳ Test Fixture'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.content}>
        <View style={styles.categoryRow}>
          <Text style={styles.categoryText}>{item.category.toUpperCase()}</Text>
          {item.rating && (
            <Text style={styles.ratingText}>★ {item.rating.toFixed(1)} ({item.reviews_count || 120})</Text>
          )}
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {item.title}
        </Text>

        <View style={styles.priceRow}>
          <Text style={styles.price}>₹{item.price_inr.toLocaleString('en-IN')}</Text>
          {item.original_price_inr && item.original_price_inr > item.price_inr && (
            <Text style={styles.originalPrice}>
              ₹{item.original_price_inr.toLocaleString('en-IN')}
            </Text>
          )}
        </View>

        {item.delivery_estimate && (
          <Text style={styles.deliveryText}>🚚 {item.delivery_estimate}</Text>
        )}

        <View style={styles.sizeRow}>
          <Text style={styles.sizeLabel}>Sizes:</Text>
          {item.available_sizes.map((s, idx) => (
            <View key={idx} style={styles.sizeChip}>
              <Text style={styles.sizeChipText}>{s}</Text>
            </View>
          ))}
        </View>

        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.buyButton} onPress={handleOpenStore}>
            <Text style={styles.buyButtonText}>Buy on {item.merchant}</Text>
          </TouchableOpacity>
          {onCritique && (
            <TouchableOpacity style={styles.critiqueButton} onPress={() => onCritique(item)}>
              <Text style={styles.critiqueButtonText}>Swap</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#151C24',
    borderRadius: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#222E3C',
    overflow: 'hidden',
  },
  imageContainer: {
    width: '100%',
    height: 200,
    backgroundColor: '#1E293B',
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  badgeRow: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  merchantBadge: {
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  merchantText: {
    color: '#F8FAFC',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sourceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  sourceText: {
    color: '#E2E8F0',
    fontSize: 10,
    fontWeight: '600',
  },
  content: {
    padding: 14,
  },
  categoryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  categoryText: {
    color: '#E5B869',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
  },
  ratingText: {
    color: '#FBBF24',
    fontSize: 11,
    fontWeight: '600',
  },
  title: {
    color: '#F1F5F9',
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 6,
  },
  price: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
    marginRight: 8,
  },
  originalPrice: {
    color: '#64748B',
    fontSize: 13,
    textDecorationLine: 'line-through',
  },
  deliveryText: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 10,
  },
  sizeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sizeLabel: {
    color: '#64748B',
    fontSize: 11,
    marginRight: 6,
  },
  sizeChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 4,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sizeChipText: {
    color: '#CBD5E1',
    fontSize: 10,
    fontWeight: '600',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  buyButton: {
    flex: 3,
    backgroundColor: '#E5B869',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  buyButtonText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  critiqueButton: {
    flex: 1,
    backgroundColor: '#1E293B',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  critiqueButtonText: {
    color: '#E2E8F0',
    fontSize: 12,
    fontWeight: '600',
  },
});
