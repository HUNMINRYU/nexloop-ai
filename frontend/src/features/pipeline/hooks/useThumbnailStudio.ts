import { useState, useEffect } from 'react';
import { generateHooks, generateThumbnailCompare } from '@/lib/api';

interface UseThumbnailStudioProps {
  selectedProduct: string;
  initialStyles?: any[];
  initialHookStrategies?: any[];
}

export function useThumbnailStudio({
  selectedProduct,
  initialStyles = [],
  initialHookStrategies = [],
}: UseThumbnailStudioProps) {
  const [styles] = useState(initialStyles);
  const [hookStrategies] = useState(initialHookStrategies);
  const [hookText, setHookText] = useState('');
  const [useHookInput, setUseHookInput] = useState(true);
  const [includeTextOverlay, setIncludeTextOverlay] = useState(true);
  const [compareItems, setCompareItems] = useState<any[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [thumbError, setThumbError] = useState('');
  const [hookLength, setHookLength] = useState('long');

  useEffect(() => {
    setHookText('');
  }, [selectedProduct]);

  const handleGenerateHook = async (styleKey: string) => {
    if (!selectedProduct) return;
    setThumbError('');
    try {
      const response = await generateHooks({
        product_name: selectedProduct,
        style: styleKey,
        count: 1,
        length: hookLength,
      });
      if (response?.hooks?.length) {
        setHookText(response.hooks[0] ?? "");
      }
    } catch (err: any) {
      setThumbError(err.message || '훅 생성에 실패했습니다.');
    }
  };

  const handleCompareStyles = async () => {
    if (!selectedProduct) {
      setThumbError('제품을 선택해주세요.');
      return;
    }
    setIsComparing(true);
    setThumbError('');
    setCompareItems([]);
    try {
      const response = await generateThumbnailCompare({
        product_name: selectedProduct,
        hook_text: hookText || undefined,
        include_text_overlay: includeTextOverlay,
        max_styles: 9,
        auto_hook_per_style: !useHookInput,
      });
      setCompareItems(response.items || []);
    } catch (err: any) {
      setThumbError(err.message || '스타일 비교 생성에 실패했습니다.');
    } finally {
      setIsComparing(false);
    }
  };

  const handleGenerateSingleThumbnail = async (styleKey: string) => {
    if (!selectedProduct) {
      setThumbError('제품을 선택해주세요.');
      return;
    }
    setThumbError('');
    // Don't clear compareItems, just append the new one
    try {
      const response = await generateThumbnailCompare({
        product_name: selectedProduct,
        hook_text: hookText || undefined,
        include_text_overlay: includeTextOverlay,
        styles: [styleKey],
        auto_hook_per_style: false, // For single gen, we usually want the current hook
      });
      if (response.items && response.items.length > 0) {
        setCompareItems((prev) => [response.items[0], ...prev]);
      }
    } catch (err: any) {
      setThumbError(err.message || '썸네일 생성에 실패했습니다.');
    }
  };

  return {
    styles,
    hookStrategies,
    hookText,
    setHookText,
    useHookInput,
    setUseHookInput,
    includeTextOverlay,
    setIncludeTextOverlay,
    compareItems,
    isComparing,
    thumbError,
    handleGenerateHook,
    handleCompareStyles,
    handleGenerateSingleThumbnail,
    hookLength,
    setHookLength,
  };
}
