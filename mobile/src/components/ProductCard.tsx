import React, { useState } from 'react';
import { View, Text, StyleSheet, Image, TouchableOpacity, Linking, Alert } from 'react-native';
import { ProductItem } from '../types';

interface ProductCardProps {
  item: ProductItem;
  onCritique?: (item: ProductItem) => void;
  selectedSize?: string;
}

export const ProductCard: React.FC<ProductCardProps> = ({ item, onCritique, selectedSize }) => {
  const [imageError, setImageError] = useState(false);

  const handleOpenStore = async () => {
    if (!item.product_url) {
      Alert.alert('Store Link', 'Direct shopping link is not available for this item.');
      return;
    }
    try {
      const supported = await Linking.canOpenURL(item.product_url);
      if (supported) {
        await Linking.openURL(item.product_url);
      } else {
        Alert.alert('Cannot Open Link', `Unable to open URL: ${item.product_url}`);
      }
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Could not launch browser.');
    }
  };

  const isVerifiedLive = item.data_source === 'live_verified';
  const isControlledFixture = item.data_source === 'controlled_fixture';

  const getCategoryIcon = (cat: string) => {
    const c = cat.toLowerCase();
    if (c.includes('top') || c.includes('shirt') || c.includes('kurta')) return '👔';
    if (c.includes('bottom') || c.includes('pant') || c.includes('trouser') || c.includes('chino')) return '👖';
    if (c.includes('shoe') || c.includes('footwear') || c.includes('sneaker') || c.includes('loafer')) return '👟';
    if (c.includes('outerwear') || c.includes('blazer') || c.includes('jacket')) return '🧥';
    if (c.includes('ethnic') || c.includes('anarkali') || c.includes('saree')) return '🥻';
    if (c.includes('accessory') || c.includes('watch') || c.includes('belt')) return '⌚';
    return '🛍️';
  };

  const hasSizeMatch = selectedSize && item.available_sizes?.length
    ? item.available_sizes.some((s) => s.toLowerCase() === selectedSize.toLowerCase())
    : null;

  return (
    <View style={styles.card}>
      <View style={styles.imageContainer}>
        {!imageError && item.image_url ? (
          <Image
            source={{ uri: item.image_url }}
            style={styles.image}
            resizeMode="cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <View style={styles.fallbackContainer}>
            <Text style={styles.fallbackIcon}>{getCategoryIcon(item.category)}</Text>
            <Text style={styles.fallbackCategory}>{item.category.toUpperCase()}</Text>
            <Text style={styles.fallbackText}>Image Preview Unavailable</Text>
          </View>
        )}

        <View style={styles.badgeRow}>
          <View style={styles.merchantBadge}>
            <Text style={styles.merchantText}>{item.merchant || 'Retailer'}</Text>
          </View>
          <View
            style={[
              styles.sourceBadge,
              {
                backgroundColor: isVerifiedLive
                  ? '#065F46'
                  : isControlledFixture
                  ? '#78350F'
                  : '#1E3A5F',
              },
            ]}
          >
            <Text style={styles.sourceText}>
              {isVerifiedLive
                ? '✓ Live Shopping'
                : isControlledFixture
                ? '⟳ Test Fixture'
                : '⚡ Cached Item'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.content}>
        <View style={styles.categoryRow}>
          <Text style={styles.categoryText}>
            {getCategoryIcon(item.category)} {item.category.toUpperCase()}
          </Text>
          {item.rating != null && (
            <Text style={styles.ratingText}>
              ★ {item.rating.toFixed(1)} {item.reviews_count ? `(${item.reviews_count})` : ''}
            </Text>
          )}
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {item.title}
        </Text>

        <View style={styles.priceRow}>
          <Text style={styles.price}>₹{item.price_inr.toLocaleString('en-IN')}</Text>
          {item.original_price_inr && item.original_price_inr > item.price_inr ? (
            <Text style={styles.originalPrice}>
              ₹{item.original_price_inr.toLocaleString('en-IN')}
            </Text>
          ) : null}
          {item.original_price_inr && item.original_price_inr > item.price_inr ? (
            <View style={styles.discountBadge}>
              <Text style={styles.discountText}>
                {Math.round(((item.original_price_inr - item.price_inr) / item.original_price_inr) * 100)}% OFF
              </Text>
            </View>
          ) : null}
        </View>

        {item.delivery_estimate ? (
          <Text style={styles.deliveryText}>🚚 Est. Delivery: {item.delivery_estimate}</Text>
        ) : null}

        {item.available_sizes && item.available_sizes.length > 0 ? (
          <View style={styles.sizeRow}>
            <Text style={styles.sizeLabel}>Sizes:</Text>
            {item.available_sizes.map((s, idx) => {
              const isMatch = selectedSize && s.toLowerCase() === selectedSize.toLowerCase();
              return (
                <View
                  key={idx}
                  style={[styles.sizeChip, isMatch && styles.sizeChipMatched]}
                >
                  <Text style={[styles.sizeChipText, isMatch && styles.sizeChipTextMatched]}>
                    {s}
                  </Text>
                </View>
              );
            })}
            {hasSizeMatch === false && (
              <Text style={styles.sizeWarningText}>(Size {selectedSize} not verified)</Text>
            )}
          </View>
        ) : (
          <View style={styles.sizeRow}>
            <Text style={styles.sizeLabel}>Sizes:</Text>
            <Text style={styles.sizeUnavailable}>Standard fit / check store</Text>
          </View>
        )}

        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={[styles.buyButton, !item.product_url && styles.buttonDisabled]}
            onPress={handleOpenStore}
            disabled={!item.product_url}
          >
            <Text style={styles.buyButtonText}>Buy on {item.merchant || 'Store'} →</Text>
          </TouchableOpacity>
          {onCritique && (
            <TouchableOpacity style={styles.critiqueButton} onPress={() => onCritique(item)}>
              <Text style={styles.critiqueButtonText}>Critique / Swap</Text>
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
    backgroundColor: '#0F1318',
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  fallbackContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1E2530',
    padding: 16,
  },
  fallbackIcon: {
    fontSize: 38,
    marginBottom: 6,
  },
  fallbackCategory: {
    color: '#E5B869',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1,
  },
  fallbackText: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
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
    backgroundColor: 'rgba(15, 23, 42, 0.88)',
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
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
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
    fontWeight: '800',
    letterSpacing: 0.8,
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
    gap: 8,
  },
  price: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '800',
  },
  originalPrice: {
    color: '#64748B',
    fontSize: 13,
    textDecorationLine: 'line-through',
  },
  discountBadge: {
    backgroundColor: '#064E3B',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  discountText: {
    color: '#34D399',
    fontSize: 10,
    fontWeight: '700',
  },
  deliveryText: {
    color: '#94A3B8',
    fontSize: 11,
    marginBottom: 10,
  },
  sizeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 4,
    marginBottom: 12,
  },
  sizeLabel: {
    color: '#64748B',
    fontSize: 11,
    marginRight: 4,
    fontWeight: '600',
  },
  sizeChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sizeChipMatched: {
    backgroundColor: '#065F46',
    borderColor: '#10B981',
  },
  sizeChipText: {
    color: '#CBD5E1',
    fontSize: 10,
    fontWeight: '600',
  },
  sizeChipTextMatched: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  sizeWarningText: {
    color: '#F59E0B',
    fontSize: 10,
    marginLeft: 4,
  },
  sizeUnavailable: {
    color: '#64748B',
    fontSize: 11,
    fontStyle: 'italic',
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
  buttonDisabled: {
    opacity: 0.5,
  },
  buyButtonText: {
    color: '#0F1318',
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  critiqueButton: {
    flex: 2,
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
