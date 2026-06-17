> Archived as complete together with the matching `market-data-api` runtime-upgrade implementation and verification included in this PR branch.

- [x] 1.1 Modify `market-data` requirements to state that the dedicated Ruby service runtime may be upgraded while preserving existing public market-data contracts.
- [x] 1.2 Modify `news` requirements to preserve protected coin-news behavior during the Ruby service runtime upgrade.
- [x] 1.3 Modify `background-jobs` requirements to preserve snapshot-refresh background behavior and observability during the runtime upgrade.
- [x] 1.4 Add a design document covering target runtime versions, direct-upgrade risks, configuration changes, dependency strategy, verification plan, and rollback expectations.
- [x] 1.5 Validate the OpenSpec change with `openspec validate change-market-data-api-to-latest-rails --strict`.

- [x] 2.1 Upgrade the Ruby version, Rails version, and directly related framework dependencies used by `market-data-api`.
- [x] 2.2 Update service bootstrapping, configuration files, and runtime conventions required by the upgraded Rails stack.
- [x] 2.3 Update provider clients, service classes, controllers, caching hooks, and Rake tasks only where required for compatibility with the upgraded runtime.
- [x] 2.4 Update test setup and supporting dependencies so the Ruby service test suite can run under the upgraded runtime.
- [x] 2.5 Resolve dependency, native-extension, and platform issues required to install and boot the upgraded Ruby service consistently in development and CI.
- [x] 2.6 Preserve the observable request and background behavior for `market-overview`, `assets/search`, `news`, and reusable snapshot refresh.
- [x] 2.7 Update directly related runtime or setup documentation for the upgraded Ruby/Rails service.

- [x] 3.1 Run focused Ruby controller and service tests covering market overview, asset search, coin news, and snapshot refresh behavior.
- [x] 3.2 Run additional Ruby checks needed to verify the upgraded dependency and runtime setup.
- [x] 3.3 Validate the OpenSpec change with `openspec validate change-market-data-api-to-latest-rails --strict`.
