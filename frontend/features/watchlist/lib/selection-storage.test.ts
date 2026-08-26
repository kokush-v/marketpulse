import { getStoredSelectedAssetId, setStoredSelectedAssetId } from "@/features/watchlist/lib/selection-storage";

describe("selection storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns null when no selected asset is stored", () => {
    expect(getStoredSelectedAssetId()).toBeNull();
  });

  it("stores and returns the selected asset id", () => {
    setStoredSelectedAssetId("bitcoin");

    expect(window.localStorage.getItem("mp_watchlist_selected_asset")).toBe("bitcoin");
    expect(getStoredSelectedAssetId()).toBe("bitcoin");
  });

  it("removes the selected asset id when cleared", () => {
    setStoredSelectedAssetId("bitcoin");
    setStoredSelectedAssetId(null);

    expect(window.localStorage.getItem("mp_watchlist_selected_asset")).toBeNull();
    expect(getStoredSelectedAssetId()).toBeNull();
  });
});
