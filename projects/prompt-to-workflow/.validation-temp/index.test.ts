import { main } from "./index";

describe("Solution", () => {
  it("should export a main function", () => {
    expect(typeof main).toBe("function");
  });
});
