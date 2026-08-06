import { recurrenceRepository, taskRepository } from '../repositories'
import { RecurrenceType, RecurrenceFreq } from '../domain/entities/enums'

/**
 * Вычисляет следующую дату инстанса по правилу шаблона.
 * Учитывает edge cases: конец месяца, timezone (упрощённо — оперирует
 * в TZ шаблона, дата хранится как локальная ISO без смещения серверного часового пояса).
 */
export function computeNextOccurrence(fromDate, rule) {
  const d = new Date(fromDate)
  switch (rule.freq) {
    case RecurrenceFreq.DAILY:
      d.setDate(d.getDate() + (rule.interval || 1))
      return d
    case RecurrenceFreq.WEEKLY:
      d.setDate(d.getDate() + 7 * (rule.interval || 1))
      return d
    case RecurrenceFreq.MONTHLY: {
      const targetMonth = d.getMonth() + (rule.interval || 1)
      const targetDay = rule.byMonthDay || d.getDate()
      const candidate = new Date(d.getFullYear(), targetMonth, targetDay)
      // Edge case: если целевой день не существует в месяце (напр. 31 в апреле) —
      // JS Date автоматически перекатывает на следующий месяц; корректируем на последний день.
      if (candidate.getMonth() !== ((targetMonth % 12) + 12) % 12) {
        return new Date(d.getFullYear(), targetMonth + 1, 0) // последний день предыдущего месяца от перекатившегося
      }
      return candidate
    }
    default:
      d.setDate(d.getDate() + (rule.interval || 1))
      return d
  }
}

export class RecurrenceService {
  async generateNextInstance(template, fromTask) {
    const nextDate = computeNextOccurrence(fromTask?.dueDate || new Date().toISOString(), template.rule)
    const newTask = await taskRepository.create({
      listId: template.listId,
      title: template.titleTemplate,
      dueDate: nextDate.toISOString(),
      recurrenceTemplateId: template.id,
      assigneeId: fromTask?.assigneeId || null,
    })
    await recurrenceRepository.update(template.id, { lastGeneratedInstanceDate: nextDate.toISOString() })
    return newTask
  }

  async onTaskCompleted(task) {
    if (!task.recurrenceTemplateId) return null
    const template = await recurrenceRepository.getById(task.recurrenceTemplateId)
    if (!template) return null
    if (template.type === RecurrenceType.COMPLETION_BASED) {
      return this.generateNextInstance(template, task)
    }
    return null // fixed_schedule генерируется заранее, не по завершению
  }
}

export const recurrenceService = new RecurrenceService()
