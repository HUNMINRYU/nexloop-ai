import { Button, Card, Input } from '@/components/ui';

interface ThumbnailStudioSectionProps {
    selectedProduct: string;
    products: string[];
    setSelectedProduct: (val: string) => void;
    hookText: string;
    setHookText: (val: string) => void;
    hookStrategies: any[];
    useHookInput: boolean;
    setUseHookInput: (val: boolean) => void;
    includeTextOverlay: boolean;
    setIncludeTextOverlay: (val: boolean) => void;
    compareItems: any[];
    isComparing: boolean;
    thumbError: string;
    handleGenerateHook: (styleKey: string) => void;
    handleCompareStyles: () => void;
}

export function ThumbnailStudioSection({
    selectedProduct,
    products,
    setSelectedProduct,
    hookText,
    setHookText,
    hookStrategies,
    useHookInput,
    setUseHookInput,
    includeTextOverlay,
    setIncludeTextOverlay,
    compareItems,
    isComparing,
    thumbError,
    handleGenerateHook,
    handleCompareStyles,
}: ThumbnailStudioSectionProps) {
    return (
        <div className="space-y-10 animate-in fade-in duration-1000">
            {/* Studio Header: Strategic Input Area */}
            <Card className="p-8 bg-white border-2 border-slate-100 shadow-2xl rounded-[32px] overflow-hidden relative">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16 blur-3xl" />

                <div className="relative z-10">
                    <header className="mb-8">
                        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">Creative Workshop</h3>
                        <p className="text-sm text-slate-500 font-medium">
                            Configure your visual strategy and generate high-converting style variants.
                        </p>
                    </header>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                        <div className="space-y-3">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">
                                Focus Product
                            </label>
                            <select
                                className="w-full h-14 bg-slate-50 border-2 border-slate-100 rounded-2xl px-4 font-bold text-slate-700 focus:border-primary/50 focus:ring-0 transition-all outline-none appearance-none cursor-pointer hover:bg-slate-100"
                                value={selectedProduct}
                                onChange={(e) => setSelectedProduct(e.target.value)}
                            >
                                {products.length === 0 && <option>No Product Found</option>}
                                {products.map((p) => (
                                    <option key={p} value={p}>
                                        {p}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">
                                Headline Strategy
                            </label>
                            <Input
                                className="w-full h-14 bg-slate-50 border-2 border-slate-100 rounded-2xl px-4 font-bold text-slate-700 transition-all"
                                value={hookText}
                                onChange={(e) => setHookText(e.target.value)}
                                placeholder="Enter a scroll-topping hook..."
                            />
                        </div>
                    </div>

                    <div className="space-y-4 mb-8">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">
                            Style Presets
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {hookStrategies.map((s) => (
                                <button
                                    key={s.key}
                                    type="button"
                                    onClick={() => handleGenerateHook(s.key)}
                                    className="px-5 py-2.5 rounded-full bg-slate-50 border-2 border-slate-100 text-sm font-bold text-slate-600 hover:border-primary/40 hover:bg-primary/5 hover:text-primary transition-all active:scale-95 flex items-center gap-2"
                                >
                                    <span className="text-lg">{s.emoji || '✨'}</span>
                                    {s.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pt-6 border-t border-slate-50">
                        <div className="flex gap-6">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    className="w-5 h-5 rounded-md border-2 border-slate-200 text-primary focus:ring-primary transition-all"
                                    checked={useHookInput}
                                    onChange={(e) => setUseHookInput(e.target.checked)}
                                />
                                <span className="text-sm font-bold text-slate-600 group-hover:text-slate-900 transition-colors">
                                    Manual Input
                                </span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    className="w-5 h-5 rounded-md border-2 border-slate-200 text-primary focus:ring-primary transition-all"
                                    checked={includeTextOverlay}
                                    onChange={(e) => setIncludeTextOverlay(e.target.checked)}
                                />
                                <span className="text-sm font-bold text-slate-600 group-hover:text-slate-900 transition-colors">
                                    Text Overlay
                                </span>
                            </label>
                        </div>

                        <Button
                            size="lg"
                            onClick={handleCompareStyles}
                            disabled={isComparing}
                            className={`h-14 px-10 rounded-2xl font-black text-base shadow-xl transition-all ${isComparing ? 'opacity-70 bg-slate-400' : 'bg-slate-900 hover:bg-slate-800'}`}
                        >
                            {isComparing ? (
                                <div className="flex items-center gap-3">
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Generating Analysis...
                                </div>
                            ) : (
                                'Generate 9 Style Variants'
                            )}
                        </Button>
                    </div>

                    {thumbError && (
                        <p className="mt-4 text-sm font-bold text-rose-500 animate-bounce">⚠️ {thumbError}</p>
                    )}
                </div>
            </Card>

            {/* Analysis Results: Grid Gallery Area */}
            <div className="space-y-6">
                <div className="flex items-center justify-between px-2">
                    <h4 className="text-xl font-black text-slate-900 tracking-tight">Variant Comparison Gallery</h4>
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#0ca678] bg-[#0ca678]/10 px-3 py-1 rounded-full">
                        9 Styles Ready
                    </span>
                </div>

                <div className="grid gap-6 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                    {compareItems.length === 0 &&
                        Array.from({ length: 9 }).map((_, i) => (
                            <div
                                key={i}
                                className="aspect-[9/16] bg-slate-100 rounded-3xl animate-pulse flex items-center justify-center p-6 border-2 border-slate-50"
                            >
                                <div className="text-center space-y-2">
                                    <div className="w-10 h-10 bg-slate-200 rounded-full mx-auto" />
                                    <div className="w-16 h-2 bg-slate-200 rounded-full mx-auto" />
                                </div>
                            </div>
                        ))}

                    {compareItems.map((item, idx) => (
                        <div
                            key={idx}
                            className="group relative flex flex-col gap-3 animate-in fade-in zoom-in duration-500"
                            style={{ animationDelay: `${idx * 100}ms` }}
                        >
                            <div className="relative aspect-[9/16] overflow-hidden rounded-[28px] border-2 border-white shadow-lg group-hover:shadow-2xl transition-all duration-500 group-hover:-translate-y-2">
                                <img
                                    src={item.url}
                                    alt={item.name}
                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                <div className="absolute bottom-4 left-4 right-4 opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 transition-all duration-500">
                                    <div className="text-[10px] font-black text-white/70 uppercase tracking-widest mb-1">
                                        Preset Style
                                    </div>
                                    <div className="text-sm font-bold text-white truncate">{item.name}</div>
                                </div>
                                {/* AI Analysis Tag */}
                                <div className="absolute top-4 right-4 w-8 h-8 bg-white/20 backdrop-blur-md rounded-full border border-white/30 flex items-center justify-center text-white scale-0 group-hover:scale-100 transition-transform duration-500 font-bold text-xs">
                                    AI
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
