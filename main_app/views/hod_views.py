def get_progression_data(request):
    niveau = request.GET.get('niveau', '3ème année')
    today = datetime.now().date()
    
    # Récupérer toutes les matières du niveau sélectionné
    subjects = Subject.objects.filter(niveau=niveau)
    
    subject_list = []
    course_progress = []
    volume_horaire_total = []  # Nouveau tableau pour les volumes horaires
    
    for subject in subjects:
        subject_list.append(subject.name[:15])
        volume_horaire_total.append(subject.volume_horaire_total)  # Ajouter le volume horaire total
        
        # Calcul de la progression basé sur les séances réalisées
        seances_realisees = EmploiTemps.objects.filter(
            matiere=subject,
            type_evenement='COURS',
            date__lte=today
        ).count()
        
        # Calculer les heures réalisées (2h par séance)
        heures_realisees = seances_realisees * 2
        
        # Calculer la progression en pourcentage
        if subject.volume_horaire_total > 0:
            progression = min(int((heures_realisees / subject.volume_horaire_total) * 100), 100)
        else:
            progression = 0
            
        course_progress.append(progression)
    
    return JsonResponse({
        'subject_list': subject_list,
        'course_progress': course_progress,
        'volume_horaire_total': volume_horaire_total,  # Ajouter cette nouvelle donnée
        'total_subjects': len(subject_list)
    })
