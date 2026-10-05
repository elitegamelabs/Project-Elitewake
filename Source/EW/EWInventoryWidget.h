// Copyright Elite Game Labs. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "EWInventoryWidget.generated.h"

class UTextBlock;
class UVerticalBox;
class UEWInventoryComponent;

/** Functional first-pass inventory screen. Final art and equipment presentation will replace this layout. */
UCLASS()
class EW_API UEWInventoryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	UFUNCTION()
	void RefreshInventory();

private:
	void BuildWidgetTree();
	UEWInventoryComponent* ResolveInventory() const;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> SummaryText;

	UPROPERTY(Transient)
	TObjectPtr<UVerticalBox> ItemsBox;

	UPROPERTY(Transient)
	TObjectPtr<UEWInventoryComponent> BoundInventory;
};
