<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import versionsMarkdown from '../../../docs/versions.md?raw'

const emit = defineEmits(['close'])

const expandedVersions = ref(new Set())

function parseVersions(markdown) {
  const releases = []
  let currentRelease = null
  let currentSection = null

  for (const rawLine of markdown.split(/\r?\n/)) {
    const line = rawLine.trim()
    const releaseMatch = line.match(/^## Версия\s+(.+)$/)
    const sectionMatch = line.match(/^###\s+(.+)$/)

    if (releaseMatch) {
      currentRelease = {
        version: releaseMatch[1].trim(),
        title: '',
        sections: [],
      }
      releases.push(currentRelease)
      currentSection = null
      continue
    }

    if (!currentRelease) continue

    if (sectionMatch) {
      currentSection = { title: sectionMatch[1].trim(), paragraphs: [], items: [] }
      currentRelease.sections.push(currentSection)
      continue
    }

    if (!line || line.startsWith('---') || line.startsWith('# ')) continue

    if (!currentSection) {
      if (!currentRelease.title) currentRelease.title = line
      continue
    }

    if (line.startsWith('- ')) {
      currentSection.items.push(line.slice(2).trim())
    } else if (!line.startsWith('```') && !line.startsWith('`')) {
      currentSection.paragraphs.push(line)
    }
  }

  return releases
}

const releases = computed(() => parseVersions(versionsMarkdown))

function isExpanded(version) {
  return expandedVersions.value.has(version)
}

function toggleVersion(version) {
  const next = new Set(expandedVersions.value)
  if (next.has(version)) next.delete(version)
  else next.add(version)
  expandedVersions.value = next
}

function expandLatest() {
  if (releases.value.length) expandedVersions.value = new Set([releases.value[0].version])
}

onMounted(expandLatest)
</script>

<template>
  <Teleport to="body">
    <div class="release-overlay" @click.self="emit('close')">
      <section class="release-modal card" role="dialog" aria-modal="true" aria-labelledby="release-title">
        <header class="release-header">
          <div>
            <span class="release-eyebrow">ИСТОРИЯ ВЕРСИЙ</span>
            <h2 id="release-title">Что нового в «По Делу»</h2>
            <p>Изменения продукта и важные обновления по версиям.</p>
          </div>
          <button class="release-close" type="button" aria-label="Закрыть" @click="emit('close')">×</button>
        </header>

        <div class="release-list scroll-thin">
          <article
            v-for="(release, index) in releases"
            :key="release.version"
            class="release-item"
            :class="{ expanded: isExpanded(release.version), latest: index === 0 }"
          >
            <button class="release-toggle" type="button" @click="toggleVersion(release.version)">
              <span class="release-version-mark">{{ index === 0 ? 'NEW' : 'v' }}</span>
              <span class="release-toggle-copy">
                <strong>Версия {{ release.version }}</strong>
                <small v-if="release.title">{{ release.title }}</small>
              </span>
              <span class="release-chevron" aria-hidden="true">{{ isExpanded(release.version) ? '⌃' : '⌄' }}</span>
            </button>

            <div v-if="isExpanded(release.version)" class="release-content">
              <section v-for="section in release.sections" :key="`${release.version}-${section.title}`" class="release-section">
                <h3>{{ section.title }}</h3>
                <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
                <ul v-if="section.items.length">
                  <li v-for="item in section.items" :key="item">{{ item }}</li>
                </ul>
              </section>
            </div>
          </article>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.release-overlay {
  position: fixed; inset: 0; z-index: 400; display: flex; align-items: center; justify-content: center;
  padding: 24px; background: rgba(20, 25, 40, 0.48); backdrop-filter: blur(4px);
}
.release-modal {
  width: min(720px, 100%); max-height: min(760px, calc(100vh - 48px)); overflow: hidden;
  padding: 0; border: 1px solid rgba(79, 124, 255, 0.16); box-shadow: 0 24px 70px rgba(21, 32, 64, 0.22);
}
.release-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 24px 26px 20px;
  background: linear-gradient(135deg, #f3f6ff, #fff 68%); border-bottom: 1px solid var(--color-border);
}
.release-eyebrow { color: var(--color-primary); font-size: 10px; font-weight: 800; letter-spacing: .12em; }
.release-header h2 { margin: 6px 0 5px; font-size: 21px; letter-spacing: -0.02em; }
.release-header p { margin: 0; color: var(--color-text-muted); font-size: 12.5px; }
.release-close {
  border: 0; background: transparent; color: var(--color-text-muted); cursor: pointer; font-size: 25px;
  line-height: 1; padding: 0 2px; transition: color .15s ease, transform .15s ease;
}
.release-close:hover { color: var(--color-text); transform: rotate(8deg); }
.release-list { max-height: calc(min(760px, 100vh - 48px) - 128px); overflow-y: auto; padding: 14px 16px 18px; }
.release-item { border: 1px solid var(--color-border); border-radius: 12px; margin-bottom: 9px; overflow: hidden; background: var(--color-surface); transition: border-color .16s ease, box-shadow .16s ease; }
.release-item.latest { border-color: rgba(79, 124, 255, .32); }
.release-item.expanded { box-shadow: 0 8px 22px rgba(42, 57, 96, .07); }
.release-toggle { width: 100%; display: flex; align-items: center; gap: 12px; padding: 14px 15px; border: 0; background: transparent; color: var(--color-text); cursor: pointer; text-align: left; }
.release-toggle:hover { background: #f7f8fc; }
.release-version-mark { width: 34px; height: 24px; display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto; border-radius: 7px; background: #eef2ff; color: var(--color-primary); font-size: 9px; font-weight: 800; letter-spacing: .04em; }
.release-item.latest .release-version-mark { background: var(--color-primary); color: #fff; }
.release-toggle-copy { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.release-toggle-copy strong { font-size: 14px; }
.release-toggle-copy small { color: var(--color-text-muted); font-size: 11.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.release-chevron { margin-left: auto; color: var(--color-primary); font-size: 18px; line-height: 1; }
.release-content { padding: 0 18px 17px 61px; border-top: 1px solid #eef0f5; }
.release-section { padding-top: 14px; }
.release-section h3 { margin: 0 0 6px; font-size: 13px; color: var(--color-text); }
.release-section p, .release-section li { margin: 0 0 7px; color: var(--color-text-secondary, #626a7a); font-size: 12.5px; line-height: 1.55; }
.release-section ul { margin: 0; padding-left: 18px; }
@media (max-width: 560px) {
  .release-overlay { padding: 10px; }
  .release-header { padding: 20px 18px 17px; }
  .release-content { padding-left: 18px; }
  .release-list { padding: 10px; }
}
</style>
