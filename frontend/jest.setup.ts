import "@testing-library/jest-dom";

declare global {
  interface Window {
    matchMedia: (query: string) => MediaQueryList;
  }
}

if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }) as MediaQueryList;
}
