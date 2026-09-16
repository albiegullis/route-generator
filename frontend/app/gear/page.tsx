"use client";

import { useState, useEffect, useMemo } from "react";
import { createClient } from "@supabase/supabase-js";
import Link from "next/link";

// Initialize the Supabase client using your new environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

export default function GearComparisonPage() {
  const [activeTab, setActiveTab] = useState("shoes");
  const [shoes, setShoes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedTerrains, setSelectedTerrains] = useState<string[]>([]);

  useEffect(() => {
    async function fetchShoes() {
      try {
        const { data, error } = await supabase
          .from("shoes")
          .select("*")
          .order("id", { ascending: true });

        if (error) throw error;
        
        if (data) {
          setShoes(data);
        }
      } catch (error) {
        console.error("Error fetching shoes:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchShoes();
  }, []);

  const brands = useMemo(() => {
    return Array.from(new Set(shoes.map(shoe => shoe.brand))).sort();
  }, [shoes]);
  
  const terrains = useMemo(() => {
    return Array.from(new Set(shoes.map(shoe => shoe.terrain))).sort();
  }, [shoes]);

  const toggleBrand = (brand: string) => {
    setSelectedBrands(prev => 
      prev.includes(brand) ? prev.filter(b => b !== brand) : [...prev, brand]
    );
  };

  const toggleTerrain = (terrain: string) => {
    setSelectedTerrains(prev => 
      prev.includes(terrain) ? prev.filter(t => t !== terrain) : [...prev, terrain]
    );
  };

  const filteredShoes = shoes.filter(shoe => {
    const matchesBrand = selectedBrands.length === 0 || selectedBrands.includes(shoe.brand);
    const matchesTerrain = selectedTerrains.length === 0 || selectedTerrains.includes(shoe.terrain);
    return matchesBrand && matchesTerrain;
  });

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-black">
      <div className="max-w-6xl mx-auto">
        
        {/* --- THE NEW OVAL TOGGLE --- */}
        <div className="flex justify-center mb-10 mt-4">
          <div className="flex bg-gray-200 rounded-full p-1 w-full max-w-md shadow-inner">
            <Link 
              href="/" 
              className="flex-1 text-center py-2.5 rounded-full text-gray-500 hover:text-black font-semibold transition-all"
            >
               Route Plotter
            </Link>
            <Link 
              href="/gear" 
              className="flex-1 text-center py-2.5 rounded-full bg-black text-white font-bold transition-all shadow-sm"
            >
               Compare Gear
            </Link>
          </div>
        </div>

        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-4">Compare Running Gear</h1>
          <p className="text-gray-500">Find the perfect equipment for your next route.</p>
        </div>

        {/* Category Navigation Tabs */}
        <div className="flex justify-center space-x-4 mb-12 border-b pb-4">
          <button 
            onClick={() => setActiveTab("shoes")}
            className={`px-6 py-2 rounded-full font-bold transition-colors ${activeTab === "shoes" ? "bg-black text-white" : "bg-gray-200 text-gray-600 hover:bg-gray-300"}`}
          >
            Running Shoes
          </button>
          <button 
            onClick={() => setActiveTab("watches")}
            className={`px-6 py-2 rounded-full font-bold transition-colors ${activeTab === "watches" ? "bg-black text-white" : "bg-gray-200 text-gray-600 hover:bg-gray-300"}`}
          >
            GPS Watches
          </button>
          <button 
            onClick={() => setActiveTab("vests")}
            className={`px-6 py-2 rounded-full font-bold transition-colors ${activeTab === "vests" ? "bg-black text-white" : "bg-gray-200 text-gray-600 hover:bg-gray-300"}`}
          >
            Hydration Vests
          </button>
        </div>

        {/* Dynamic Content Area for Shoes */}
        {activeTab === "shoes" && (
          <>
            {isLoading ? (
              <div className="text-center py-20">
                <div className="animate-pulse flex flex-col items-center">
                  <div className="h-12 w-12 bg-gray-300 rounded-full mb-4"></div>
                  <p className="text-gray-500 font-semibold">Loading database...</p>
                </div>
              </div>
            ) : (
              <div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
                  
                  <div className="mb-6">
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 block">Brands</label>
                    <div className="flex flex-wrap gap-2">
                      <button 
                        onClick={() => setSelectedBrands([])}
                        className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors border ${selectedBrands.length === 0 ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"}`}
                      >
                        All
                      </button>
                      {brands.map(brand => (
                        <button 
                          key={brand as string}
                          onClick={() => toggleBrand(brand as string)}
                          className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors border ${selectedBrands.includes(brand as string) ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"}`}
                        >
                          {brand as string}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 block">Terrain</label>
                    <div className="flex flex-wrap gap-2 items-center">
                      <button 
                        onClick={() => setSelectedTerrains([])}
                        className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors border ${selectedTerrains.length === 0 ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"}`}
                      >
                        All
                      </button>
                      {terrains.map(terrain => (
                        <button 
                          key={terrain as string}
                          onClick={() => toggleTerrain(terrain as string)}
                          className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors border ${selectedTerrains.includes(terrain as string) ? "bg-black text-white border-black" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"}`}
                        >
                          {terrain as string}
                        </button>
                      ))}
                      
                      <div className="ml-auto text-sm font-semibold text-gray-500 bg-gray-100 px-4 py-1.5 rounded-full">
                        Showing {filteredShoes.length} of {shoes.length}
                      </div>
                    </div>
                  </div>
                  
                </div>

                {filteredShoes.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-xl border border-dashed border-gray-300">
                    <p className="text-xl text-gray-500 font-semibold">No shoes match these filters.</p>
                    <button 
                      onClick={() => { setSelectedBrands([]); setSelectedTerrains([]); }}
                      className="mt-4 text-blue-600 hover:text-blue-800 font-bold underline"
                    >
                      Clear filters
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {filteredShoes.map((shoe) => (
                      <div key={shoe.id} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                        <div className="h-40 bg-gray-100 rounded-xl mb-6 flex items-center justify-center text-4xl">
                          👟
                        </div>
                        <h2 className="text-2xl font-bold mb-1">{shoe.brand}</h2>
                        <h3 className="text-lg text-gray-600 mb-6">{shoe.model}</h3>
                        
                        <div className="space-y-3 text-sm">
                          <div className="flex justify-between border-b pb-2">
                            <span className="font-semibold text-gray-500">Terrain</span>
                            <span className="font-bold">{shoe.terrain}</span>
                          </div>
                          <div className="flex justify-between border-b pb-2">
                            <span className="font-semibold text-gray-500">Heel Drop</span>
                            <span className="font-bold">{shoe.drop}</span>
                          </div>
                          <div className="flex justify-between border-b pb-2">
                            <span className="font-semibold text-gray-500">Weight</span>
                            <span className="font-bold">{shoe.weight}</span>
                          </div>
                          <div className="flex justify-between border-b pb-2">
                            <span className="font-semibold text-gray-500">Cushioning</span>
                            <span className="font-bold">{shoe.cushioning}</span>
                          </div>
                          <div className="flex justify-between pt-2">
                            <span className="font-semibold text-gray-500">Retail Price</span>
                            <span className="font-bold text-lg">{shoe.price}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {activeTab === "watches" && (
          <div className="text-center py-20 text-gray-500">
            <span className="text-6xl block mb-4">⌚</span>
            <h2 className="text-2xl font-bold text-black mb-2">GPS Watches</h2>
            <p>Comparison data coming soon...</p>
          </div>
        )}

        {activeTab === "vests" && (
          <div className="text-center py-20 text-gray-500">
            <span className="text-6xl block mb-4">🎒</span>
            <h2 className="text-2xl font-bold text-black mb-2">Hydration Vests</h2>
            <p>Comparison data coming soon...</p>
          </div>
        )}

      </div>
    </div>
  );
}